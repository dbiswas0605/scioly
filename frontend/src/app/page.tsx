"use client";

import { useRouter } from "next/navigation";
import { GraduationCap, ShieldCheck, Users } from "lucide-react";

import { QuoteBanner } from "@/components/QuoteBanner";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useRole, type Role } from "@/hooks/useRole";

interface RoleCardConfig {
  role: Role;
  href: string;
  title: string;
  description: string;
  icon: typeof GraduationCap;
}

const ROLE_CARDS: RoleCardConfig[] = [
  {
    role: "student",
    href: "/practice",
    title: "Student",
    description:
      "Take timed practice exams, review your answers, and track your score improvements over time.",
    icon: GraduationCap,
  },
  {
    role: "parent",
    href: "/upload",
    title: "Parent / Teacher",
    description:
      "Upload new question papers and keep an eye on your student's exam history and trends.",
    icon: Users,
  },
  {
    role: "admin",
    href: "/admin",
    title: "Admin",
    description:
      "Manage question papers, configure the LLM provider, and set exam timers.",
    icon: ShieldCheck,
  },
];

export default function Home() {
  const { setRole } = useRole();
  const router = useRouter();

  function handleSelect(card: RoleCardConfig) {
    setRole(card.role);
    router.push(card.href);
  }

  return (
    <div className="flex w-full flex-col">
      <QuoteBanner />
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-12 px-4 py-16 sm:px-6 sm:py-20">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            Scioly Prep
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            A practice and mock-exam tool for Science Olympiad-style questions,
            built for home tutoring students. Choose how you&apos;d like to get
            started.
          </p>
        </div>

        <div className="grid w-full gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {ROLE_CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <Card
                key={card.role}
                role="button"
                tabIndex={0}
                onClick={() => handleSelect(card)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleSelect(card);
                  }
                }}
                className="group cursor-pointer transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/5 hover:ring-1 hover:ring-primary/20 focus-visible:-translate-y-1 focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:outline-none"
              >
                <CardHeader className="gap-3">
                  <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <Icon className="size-5.5" />
                  </span>
                  <CardTitle className="text-xl">{card.title}</CardTitle>
                  <CardDescription className="text-sm leading-relaxed">
                    {card.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
