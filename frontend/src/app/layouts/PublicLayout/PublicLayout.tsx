import { Outlet } from "react-router-dom";
import "./PublicLayout.css";

export function PublicLayout() {
  return (
    <main className="public-layout">
      <Outlet />
    </main>
  );
}
