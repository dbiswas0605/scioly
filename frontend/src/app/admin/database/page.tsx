import Link from "next/link";
import { ArrowLeft, Database } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DatabaseSettings } from "./DatabaseSettings";

export default function DatabaseSettingsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <Link
        href="/admin"
        className={`${buttonVariants({ variant: "ghost" })} mb-4 -ml-2`}
      >
        <ArrowLeft />
        Back to Admin
      </Link>
      <Card>
        <CardHeader>
          <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Database className="size-4.5" />
          </span>
          <CardTitle>Database Connection</CardTitle>
          <CardDescription>
            Set the PostgreSQL server that stores application data. The
            connection is tested and migrations are applied before it becomes
            active.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DatabaseSettings />
        </CardContent>
      </Card>
    </div>
  );
}
