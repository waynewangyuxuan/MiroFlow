# MiroFlow Code Execution Sandbox — 本地部署方案分析

> 基于 MiroFlow 代码库深度分析 + 行业方案调研，为 lab 环境本地沙盒部署提供决策依据。

## 1. 现状分析：MiroFlow 当前的 E2B 集成

### 当前架构

MiroFlow 的 code execution 通过 `src/tool/mcp_servers/python_server.py` 实现，作为一个 **FastMCP server** 暴露以下工具：

| Tool | 功能 |
|------|------|
| `create_sandbox` | 创建 E2B Firecracker microVM 沙盒 |
| `run_command` | 在沙盒中执行 shell 命令 |
| `run_python_code` | 在沙盒中执行 Python 代码 |
| `upload_file_from_local_to_sandbox` | 本地文件 → 沙盒 |
| `download_file_from_internet_to_sandbox` | 互联网文件 → 沙盒 |
| `download_file_from_sandbox_to_local` | 沙盒文件 → 本地 |

### 关键配置

```yaml
# config/tool/tool-code.yaml
E2B_API_KEY: "${oc.env:E2B_API_KEY}"
DEFAULT_TEMPLATE_ID: "all_pip_apt_pkg"
DEFAULT_TIMEOUT: "1800"  # 30 分钟
```

### 当前痛点

1. **云端依赖**：E2B 是 SaaS 服务，每次 `create_sandbox` 都通过 API 远程创建 Firecracker microVM
2. **延迟**：网络往返 + VM 创建，benchmark 场景下（数百个 task）累积延迟显著
3. **成本**：高频 benchmark 跑量下 E2B API 费用不可忽视
4. **可控性**：无法自定义 VM 镜像的底层行为、网络策略、资源配额
5. **包安装开销**：`COMMON_PACKAGES` 列表有 30+ 科学计算包，虽有 template 但每次新沙盒仍有初始化成本

### 接口契约（替换时需保持兼容）

替换方案必须保持 `python_server.py` 的 MCP tool 接口不变，只替换底层的 `e2b_code_interpreter.Sandbox` 调用。核心 API surface：

```python
# 创建
sandbox = Sandbox(template=..., timeout=..., api_key=...)
info = sandbox.get_info()  # → sandbox_id

# 连接
sandbox = Sandbox.connect(sandbox_id, api_key=...)

# 执行
sandbox.commands.run(command)        # shell
sandbox.run_code(code_block)         # Python

# 文件
sandbox.files.write(path, file_obj)  # 上传
sandbox.files.read(path, format=...) # 下载

# 生命周期
sandbox.set_timeout(seconds)
```

---

## 2. 方案全景对比

### 2.1 方案分级

```
┌─────────────────────────────────────────────────────────┐
│                    隔离强度 ↑                            │
│                                                         │
│  Firecracker ─── E2B ─── Microsandbox ─── Kata         │  ← Hardware VM
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  gVisor (runsc)                                         │  ← User-space kernel
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Docker + seccomp ─── DifySandbox                       │  ← Container
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  nsjail ─── bubblewrap                                  │  ← Namespace sandbox
│                                                         │
│  Landlock                                               │  ← Kernel LSM
│                                                         │
│                    启动速度 ↑                            │
└─────────────────────────────────────────────────────────┘
```

### 2.2 详细对比

| 维度 | E2B (现状) | Docker+gVisor | Firecracker (自建) | Microsandbox | nsjail | DifySandbox |
|------|-----------|---------------|-------------------|--------------|--------|-------------|
| **本地部署** | ⚠ 需 Terraform | ✅ 直接可用 | ✅ 需 KVM | ✅ 需 KVM | ✅ 纯 C | ✅ Docker |
| **隔离级别** | MicroVM | User-kernel | MicroVM | MicroVM | Namespace | Container |
| **启动延迟** | ~200ms+网络 | 300-500ms | ~125ms | <200ms | 1-10ms | 100-300ms |
| **内存开销** | <5MiB/VM | ~20MB/容器 | <5MiB/VM | Minimal | 极小 | Container级 |
| **包管理** | Template 镜像 | Docker image | 自建 rootfs | OCI image | 手动 chroot | Container |
| **网络控制** | API 配置 | Docker 网络 | Namespace | VM 边界 | Namespace | 沙盒隔离 |
| **文件传递** | API 调用 | Volume mount | Mount 配置 | Container mount | Mount namespace | 文件系统隔离 |
| **MCP 兼容** | 原生 | 需适配 | 需适配 | 原生设计 | 需适配 | 需适配 |
| **许可证** | Apache 2.0 | Apache 2.0 | Apache 2.0 | Apache 2.0 | Apache 2.0 | MIT |
| **成熟度** | 生产级 | 生产级 | 生产级(AWS) | 实验阶段(2025.5) | 成熟 | 生产级 |
| **运维复杂度** | 低(SaaS) | 中 | 高 | 低 | 高 | 低 |

### 2.3 同类 Agent 框架的选择

| 框架 | 沙盒方案 | 说明 |
|------|---------|------|
| **OpenHands** | Docker 容器 + Daytona Runtime | REST API server 跑在容器沙盒内 |
| **SWE-agent** | SWE-ReX (自研) | 支持 Docker/Modal/AWS Fargate，gVisor 隔离可选 |
| **AutoGen** | Docker (DockerCommandLineCodeExecutor) | 社区实现了 E2B 集成 |
| **Dify** | DifySandbox (自研) | Docker + seccomp，支持 Python/Node.js |

---

## 3. 针对 MiroFlow 的推荐方案

### 方案 A：Docker + gVisor（推荐起步方案）⭐

**适合阶段**：当前 research 阶段，快速替换 E2B

**核心思路**：预构建 Docker 镜像（含所有 COMMON_PACKAGES），使用 gVisor 作为 runtime 提供用户态内核隔离。

**改造量**：只需重写 `python_server.py` 中的 Sandbox 类调用，保持 MCP tool 接口不变。

```
┌──────────────────────────────────────────┐
│  python_server.py (MCP Server)           │
│  ┌────────────────────────────────────┐  │
│  │ create_sandbox() → docker run      │  │
│  │ run_command()    → docker exec     │  │
│  │ run_python_code()→ docker exec     │  │
│  │ upload_file()    → docker cp       │  │
│  │ download_file()  → docker cp       │  │
│  └────────────────────────────────────┘  │
│           ↓                              │
│  Docker Engine (runtime=runsc/gVisor)    │
│  ┌────────────────────────────────────┐  │
│  │ 预构建镜像: miroflow-sandbox       │  │
│  │ - Python 3.12 + scientific stack  │  │
│  │ - apt packages (poppler, etc.)    │  │
│  │ - 30 分钟自动回收                  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**优点**：
- 1 天内可搭建完成
- Docker 生态成熟，团队成员都熟悉
- gVisor 提供足够的隔离（用户态内核，阻断内核漏洞利用）
- 预构建镜像消除每次包安装开销
- 完全本地，零 API 费用

**缺点**：
- gVisor 对 I/O 密集操作有 10-30% 性能开销
- 隔离不如真正的 microVM

**实施成本**：~1-2 天

---

### 方案 B：Firecracker 自建（高安全需求）

**适合阶段**：需要跑不可信代码、多租户场景、或未来产品化

**核心思路**：直接使用 Firecracker 在本地创建 microVM，复刻 E2B 的底层架构但完全自控。

**改造量**：需要实现 Firecracker API wrapper，管理 VM 生命周期。

**优点**：
- 与 E2B 同级隔离（就是 E2B 的底层技术）
- 125ms 启动，<5MiB 内存/VM
- 完全自控，可定制内核、网络、存储

**缺点**：
- 需要 KVM 支持的 Linux 主机
- 需要管理 kernel image + rootfs
- 运维复杂度最高
- 不适合 macOS 开发环境（需要 Linux server）

**实施成本**：~1-2 周

---

### 方案 C：Microsandbox（前沿但有风险）

**适合阶段**：中期迁移目标，等它稳定后替换

**核心思路**：2025 年 5 月发布的 libkrun 微 VM 方案，专为 AI agent 设计，原生支持 MCP。

**优点**：
- 专为 AI agent 场景设计
- MCP 原生集成
- OCI 镜像兼容（复用 Docker 镜像）
- Apache 2.0 许可

**缺点**：
- 非常新（2025.5），标记为 experimental
- 社区小，文档不完善
- 需要 KVM 支持

**建议**：关注但暂不采用，作为 Phase 2 迁移候选。

---

### 方案 D：nsjail（极致轻量）

**适合阶段**：对延迟极度敏感的场景

**优点**：1-10ms 启动，Google 内部使用
**缺点**：配置复杂，需要自己管理 rootfs 和依赖，隔离弱于 VM

---

## 4. 推荐实施路线

```
Phase 1 (当前)          Phase 2 (3个月后)         Phase 3 (6个月后)
─────────────         ─────────────────        ──────────────────
Docker + gVisor        Firecracker 自建          Microsandbox 评估
                       或 Session Pool
                       优化

- 替换 E2B 云端依赖      - 按需升级隔离级别         - 跟踪社区成熟度
- 预构建科学计算镜像      - 实现沙盒复用/预热         - MCP 原生集成
- 保持 MCP 接口不变      - 连接池减少创建开销         - 贡献上游
- 零 API 成本          - benchmark 性能优化
```

### Phase 1 具体步骤

1. **构建 Docker 镜像** `miroflow-sandbox:latest`
   - 基于 Python 3.12
   - 预装所有 `COMMON_PACKAGES` 和 `SYSTEM_PACKAGES`
   - 设置默认工作目录 `/home/user`

2. **安装 gVisor runtime**
   ```bash
   # 在 lab server 上
   sudo runsc install
   sudo systemctl restart docker
   ```

3. **重写 `python_server.py` 底层调用**
   - 将 `e2b_code_interpreter.Sandbox` 替换为 `docker` SDK 调用
   - 保持所有 6 个 MCP tool 的接口签名不变
   - 实现 `sandbox_id` → `container_id` 的映射

4. **配置更新**
   ```yaml
   # config/tool/tool-code.yaml
   env:
     SANDBOX_BACKEND: "docker-gvisor"  # 或 "e2b" 保持兼容
     DOCKER_RUNTIME: "runsc"
     SANDBOX_IMAGE: "miroflow-sandbox:latest"
     DEFAULT_TIMEOUT: "1800"
   ```

5. **验证**：在 GAIA benchmark 上对比 E2B vs Docker+gVisor 的 score 一致性

---

## 5. 关键决策点

| 决策 | 选项 | 建议 |
|------|------|------|
| Lab server 是否支持 KVM？ | 是 → Firecracker/Microsandbox 可选 | 确认后决定 Phase 2 路线 |
| 开发环境是 macOS 还是 Linux？ | macOS → Docker Desktop + 无 gVisor | 开发用 Docker，CI/benchmark 用 gVisor |
| 沙盒需要访问互联网吗？ | benchmark 需要（wget 下载文件） | Docker 网络策略：允许出站，禁止入站 |
| 是否需要沙盒复用/session pool？ | Phase 1 不需要，Phase 2 考虑 | 先保证功能正确，再优化性能 |
| 是否考虑产品化多租户？ | 当前 research 阶段不需要 | 如果需要，直接上 Firecracker |

---

## 6. 参考资源

- [E2B 开源仓库](https://github.com/e2b-dev/E2B) — 可参考其 Firecracker 编排逻辑
- [gVisor 文档](https://gvisor.dev/docs/) — Docker runtime 配置
- [Firecracker GitHub](https://github.com/firecracker-microvm/firecracker)
- [Microsandbox](https://github.com/zerocore-ai/microsandbox) — 关注其 MCP 集成进展
- [SWE-ReX](https://github.com/SWE-agent/SWE-ReX) — SWE-agent 的沙盒方案，可参考架构
- [DifySandbox](https://github.com/langgenius/dify-sandbox) — Dify 的开源沙盒实现
- OpenHands Runtime 文档 — Docker 沙盒 + REST API 架构

---

*分析日期：2026-02-27*
*基于 MiroFlow 代码库 commit 当前版本*
