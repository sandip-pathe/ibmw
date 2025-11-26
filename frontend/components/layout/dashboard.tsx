import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-black text-gray-100">
      <Sidebar />
      <div className="pl-64">
        {/* Header could go here */}
        {children}
      </div>
    </div>
  );
}
