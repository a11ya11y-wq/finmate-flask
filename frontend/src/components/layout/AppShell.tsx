import { useEffect, useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";
import { useAuthStore } from "../../store/authStore";

const navItems = [
	{ to: "/dashboard", label: "Dashboard" },
	{ to: "/budgets", label: "Budgets" },
	{ to: "/profile", label: "Profile" }
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
		<div className="min-h-screen bg-[#0a0e17]">
			<header className="border-b border-white/10 bg-[#0b0f17]/80 backdrop-blur">
				<div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
					<Link to="/dashboard" className="flex items-center gap-3">
						<img src="/img/finmatelogo1.png" alt="FinMate" className="h-8 w-8" />
						<span className="text-lg font-semibold text-slate-100">FinMate</span>
					</Link>
					<div className="relative" ref={menuRef}>
						<button
							type="button"
							className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200"
							onClick={() => setOpen((prev) => !prev)}
						>
							<img
								src={`/${user?.avatar ?? "avatars/default/default.svg"}`}
								alt="Avatar"
								className="h-9 w-9 rounded-full border border-blue-500/30"
							/>
							<span className="hidden text-sm font-medium text-slate-100 sm:block">
								{user?.username ?? "User"}
							</span>
							<i className="bi bi-chevron-down text-slate-400" />
						</button>
						{open && (
							<div className="absolute right-0 mt-3 w-48 rounded-2xl border border-white/10 bg-[#0b0f17] p-2 shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
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
										{item.label}
									</NavLink>
								))}
								<button
									type="button"
									className="mt-2 w-full rounded-xl px-3 py-2 text-left text-sm text-red-300 hover:bg-red-500/10"
									onClick={logout}
								>
									Logout
								</button>
							</div>
						)}
					</div>
				</div>
			</header>
			<main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
		</div>
	);
};

export default AppShell;

