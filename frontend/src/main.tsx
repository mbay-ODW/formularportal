import React from "react";
import ReactDOM from "react-dom/client";
import { match, usePath } from "./router";
import "./styles.css";
import { AdminLayout } from "./pages/Admin";
import Dashboard from "./pages/Dashboard";
import Einstellungen from "./pages/Einstellungen";
import FormularAdmin from "./pages/FormularAdmin";
import Katalog from "./pages/Katalog";
import PublicForm from "./pages/PublicForm";
import PublicPortal from "./pages/PublicPortal";
import VorgangPage from "./pages/VorgangPage";

function App() {
  const path = usePath();
  let m;
  // Kundenportal (ohne Login)
  if ((m = match("/p/:token", path))) return <PublicPortal token={m.token} />;
  if ((m = match("/f/:token", path))) return <PublicForm token={m.token} />;

  // Verwaltung (hinter Authelia)
  let page: React.ReactNode;
  if ((m = match("/vorgang/:id", path))) page = <VorgangPage id={Number(m.id)} />;
  else if ((m = match("/formular/:id", path))) page = <FormularAdmin id={Number(m.id)} />;
  else if ((m = match("/katalog/:key", path))) page = <Katalog formKey={m.key} />;
  else if (path === "/katalog") page = <Katalog />;
  else if (path === "/einstellungen") page = <Einstellungen />;
  else page = <Dashboard />;
  return <AdminLayout path={path}>{page}</AdminLayout>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App /></React.StrictMode>,
);
