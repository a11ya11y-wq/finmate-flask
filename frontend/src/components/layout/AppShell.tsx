import { useEffect, useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";
import { useAuthStore } from "../../store/authStore";

const navItems = [
	{ to: "/dashboard", label: "Dashboard", icon: "bi-speedometer2" },
	{ to: "/budgets", label: "Budgets", icon: "bi-wallet2" },
	{ to: "/reports", label: "Reports", icon: "bi-graph-up" },
	{ to: "/profile", label: "Profile", icon: "bi-person" }
];

type AppShellProps = {
	children: React.ReactNode;
};

const AppShell = ({ children }: AppShellProps) => {
	const { user, logout } = useAuthStore();
	const [open, setOpen] = useState(false);
	const menuRef = useRef<HTMLDivElement | null>(null);

	useEffect(() => {
		const handleClick = (event: MouseEvent) => {
			if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
				setOpen(false);
			}
		};

		document.addEventListener("mousedown", handleClick);
		return () => document.removeEventListener("mousedown", handleClick);
	}, []);

	return (
		<div className="min-h-screen bg-[#0a0e17] pb-20 sm:pb-0">
			<header className="relative z-50 border-b border-white/10 bg-[#0b0f17]/80 backdrop-blur">
				<div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
					<Link to="/dashboard" className="flex items-center gap-3">
					<img src="/img/finmatelogo1.png" alt="FinMate" className="h-10 w-10 sm:h-16 sm:w-16 md:h-20 md:w-20" />
				</Link>
					{/* Мобільний аватар — просто посилання на профіль, без дропдауну */}
				<Link
					to="/profile"
					className="flex sm:hidden items-center justify-center"
				>
					<img
						data-testid="user-avatar"
						src={`/${user?.avatar ?? "avatars/default/default.svg"}`}
						alt="Avatar"
						className="h-9 w-9 rounded-full border-2 border-blue-500/40"
					/>
				</Link>

				{/* Десктопний дропдаун */}
				<div className="relative hidden sm:block" ref={menuRef}>
					<button
						data-testid="user-menu-toggle"
						type="button"
						className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200"
						onClick={() => setOpen((prev) => !prev)}
					>
						<img
							src={`/${user?.avatar ?? "avatars/default/default.svg"}`}
							alt="Avatar"
							className="h-9 w-9 rounded-full border border-blue-500/30"
						/>
						<span data-testid="user-name" className="text-sm font-medium text-slate-100">
							{user?.username ?? "User"}
						</span>
						<i className="bi bi-chevron-down text-slate-400" />
					</button>
					{open && (
						<div data-testid="user-menu-container" className="absolute right-0 mt-3 w-48 rounded-2xl border border-white/10 bg-[#0b0f17] p-2 shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
							{navItems.map((item) => (
								<NavLink
									key={item.to}
									to={item.to}
									className={({ isActive }) =>
										cn(
											"flex items-center gap-2 rounded-xl px-3 py-2 text-sm",
											isActive
												? "bg-blue-500/15 text-blue-200"
												: "text-slate-300 hover:bg-white/5"
										)
									}
									onClick={() => setOpen(false)}
								>
									<i className={`bi ${item.icon} text-lg`} />
									{item.label}
								</NavLink>
							))}
							<div className="my-2 h-px bg-white/10" />
							<button
								type="button"
								className="mt-2 w-full flex items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-red-300 hover:bg-red-500/10"
								data-testid="logout-button"
								onClick={logout}
							>
								<i className="bi bi-box-arrow-right text-lg" />
								Logout
							</button>
						</div>
					)}
				</div>
				</div>
			</header>

			<main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">{children}</main>

            {/* Mobile Bottom Navigation Bar */}
            <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around border-t border-white/10 bg-[#0b0f17]/90 px-2 py-3 backdrop-blur-xl sm:hidden">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                            cn(
                                "flex flex-col items-center gap-1 rounded-xl px-4 py-2 transition-colors",
                                isActive
                                    ? "text-blue-400"
                                    : "text-slate-500 hover:text-slate-300"
                            )
                        }
                    >
                        <i className={`bi ${item.icon} text-xl`} />
                        <span className="text-[10px] font-medium tracking-wide">{item.label}</span>
                    </NavLink>
                ))}
            </nav>
		</div>
	);
};

export default AppShell;
