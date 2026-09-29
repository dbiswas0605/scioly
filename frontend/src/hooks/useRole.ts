import { useContext } from "react";
import { RoleContext, type Role, type RoleContextValue } from "@/context/RoleContext";

export type { Role, RoleContextValue };

export function useRole(): RoleContextValue {
  const context = useContext(RoleContext);
  if (context === undefined) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
