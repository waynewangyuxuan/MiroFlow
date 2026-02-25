import { NavLink, Outlet } from 'react-router-dom'
import { Database, Activity, FlaskConical } from 'lucide-react'
import { color, font, size } from '../styles/tokens'

const S = {
  shell: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: '32px',
    padding: '0 32px',
    height: '52px',
    borderBottom: `1px solid ${color.border}`,
    background: color.surface,
  },
  logo: {
    fontSize: size.md,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.03em',
    marginRight: '8px',
  },
  divider: {
    width: '1px',
    height: '20px',
    background: color.border,
  },
  links: {
    display: 'flex',
    gap: '4px',
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    borderRadius: '6px',
    fontSize: size.sm,
    fontWeight: 500,
    color: color.textMuted,
    textDecoration: 'none',
    transition: 'all 0.12s ease',
    letterSpacing: '-0.01em',
  },
  linkActive: {
    color: color.accent,
    background: '#2D5A470A',
  },
  main: {
    flex: 1,
    padding: '28px 32px',
    maxWidth: '1440px',
    margin: '0 auto',
    width: '100%',
  },
}

const navItems = [
  { to: '/', icon: Database, label: 'Benchmark Data' },
  { to: '/traces', icon: Activity, label: 'Trace Logs' },
  { to: '/experiments', icon: FlaskConical, label: 'Experiments' },
]

export default function Layout() {
  return (
    <div style={S.shell}>
      <nav style={S.nav}>
        <span style={S.logo}>MiroFlow</span>
        <div style={S.divider} />
        <div style={S.links}>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                ...S.link,
                ...(isActive ? S.linkActive : {}),
              })}
            >
              <Icon size={14} strokeWidth={1.8} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
      <main style={S.main}>
        <Outlet />
      </main>
    </div>
  )
}
