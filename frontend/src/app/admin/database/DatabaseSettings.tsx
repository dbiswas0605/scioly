"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorMessage } from "@/lib/api/client";
import {
  getDatabaseConnection,
  updateDatabaseConnection,
} from "@/lib/api/admin";
import type { DatabaseConnection } from "@/lib/api/types";

export function DatabaseSettings() {
  const [host, setHost] = useState("192.168.1.188");
  const [port, setPort] = useState("5433");
  const [database, setDatabase] = useState("scioly");
  const [username, setUsername] = useState("scioly");
  const [password, setPassword] = useState("");
  const [connection, setConnection] = useState<DatabaseConnection | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getDatabaseConnection()
      .then((current) => {
        if (cancelled) return;
        setConnection(current);
        if (current.updated_at) {
          setHost(current.host);
          setPort(String(current.port));
          setDatabase(current.database);
          setUsername(current.username);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(getErrorMessage(err, "Could not load database connection settings."));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave() {
    const parsedPort = Number(port);
    if (!Number.isInteger(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
      setError("Enter a valid port number from 1 to 65535.");
      return;
    }
    if (!password && !connection?.has_password) {
      setError("Enter the PostgreSQL password to configure this connection.");
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await updateDatabaseConnection({
        host: host.trim(),
        port: parsedPort,
        database: database.trim(),
        username: username.trim(),
        ...(password ? { password } : {}),
      });
      setConnection(updated);
      setPassword("");
      setSaved(true);
    } catch (err) {
      setError(getErrorMessage(err, "Could not connect to this database."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {connection?.is_active ? (
        <div className="rounded-lg border bg-muted/30 p-3 text-sm">
          Active database:{" "}
          <strong>
            {connection.username}@{connection.host}:{connection.port}/{connection.database}
          </strong>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="grid gap-1.5">
          <Label htmlFor="database-host">Hostname or IP</Label>
          <Input
            id="database-host"
            autoComplete="off"
            value={host}
            onChange={(event) => setHost(event.target.value)}
            disabled={loading || saving}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="database-port">Port</Label>
          <Input
            id="database-port"
            type="number"
            min={1}
            max={65535}
            value={port}
            onChange={(event) => setPort(event.target.value)}
            disabled={loading || saving}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="database-name">Database</Label>
          <Input
            id="database-name"
            autoComplete="off"
            value={database}
            onChange={(event) => setDatabase(event.target.value)}
            disabled={loading || saving}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="database-username">Username</Label>
          <Input
            id="database-username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={loading || saving}
          />
        </div>
        <div className="grid gap-1.5 sm:col-span-2">
          <Label htmlFor="database-password">Password</Label>
          <Input
            id="database-password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={loading || saving}
            placeholder={
              connection?.has_password
                ? "Saved password — leave blank to keep it"
                : "Enter PostgreSQL password"
            }
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        The password is stored in the local configuration database and never
        returned by the API. The target database is migrated and seeded
        idempotently; existing records are not overwritten. This app does not
        yet have authentication, so only expose Admin on a trusted network.
      </p>

      <Button
        onClick={handleSave}
        disabled={loading || saving}
        className="w-fit gap-2"
      >
        {saving ? <Loader2 className="size-4 animate-spin" /> : null}
        {saving ? "Testing and connecting…" : "Test and connect"}
      </Button>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {saved ? (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
          <p className="mb-3 flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="size-4" />
            Connected. Found {connection?.tables.length ?? 0} tables with{" "}
            {connection?.total_records.toLocaleString() ?? 0} total records.
          </p>
          {connection?.tables.length ? (
            <ul className="grid gap-2 sm:grid-cols-2">
              {connection.tables.map((table) => (
                <li
                  key={table.name}
                  className="flex items-center justify-between gap-3 rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <code>{table.name}</code>
                  <span className="text-muted-foreground">
                    {table.record_count.toLocaleString()} records
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              No tables were found in the public schema.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
