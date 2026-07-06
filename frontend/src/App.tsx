import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { Overview } from "@/pages/Overview";
import { Workload } from "@/pages/Workload";
import { Rules } from "@/pages/Rules";
import { Activity } from "@/pages/Activity";

function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1120px] px-8 py-7">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/w/:key" element={<Workload />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="*" element={<Overview />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
