# Phase 4: Frontend UI Integration

## Objective
Port and integrate the existing `./Frontend-prototype` Google Stitch code into a clean Next.js 14+ structure with the Quantum Synthetic design system. Create an interactive telemetry dashboard with three main visual tabs: Hardware Model, Compiler Optimization, and Evaluation Metrics.

---

## Prerequisites
- Phase 3: FastAPI backend with all endpoints functional
- Node.js 18+ installed
- Working Q-Weave API at `http://localhost:8000`

---

## Architecture Overview

```
qweave_ui/
├── app/                          # Next.js 14+ App Router
│   ├── layout.tsx               # Root layout with fonts, metadata
│   ├── page.tsx                 # Dashboard page (redirects to hardware)
│   ├── hardware/                # Tab 1: Hardware Model
│   │   └── page.tsx
│   ├── compiler/                # Tab 2: Compiler Pass
│   │   └── page.tsx
│   ├── evaluation/              # Tab 3: Evaluation Metrics
│   │   └── page.tsx
│   └── globals.css              # Global styles, Tailwind imports
├── components/                   # React components
│   ├── layout/
│   │   ├── Sidebar.tsx          # Left sidebar navigation
│   │   ├── Header.tsx           # Top header bar
│   │   └── SubNavigation.tsx    # Tab navigation within pages
│   ├── hardware/
│   │   ├── NetworkGraph.tsx     # Interactive topology graph
│   │   ├── InteractionMatrix.tsx # Matrix table component
│   │   └── StatsCard.tsx        # Small stat cards
│   ├── compiler/
│   │   ├── SchedulePanel.tsx    # Side-by-side schedule view
│   │   ├── GateBlock.tsx        # Individual gate sequence block
│   │   └── DiffLegend.tsx       # Change legend for mitigated gates
│   ├── evaluation/
│   │   ├── MetricCard.tsx       # Telemetry cards
│   │   ├── BarChart.tsx         # Success probability bar chart
│   │   └── ComparisonTable.tsx  # Detailed metrics table
│   └── common/
│       ├── Button.tsx           # Styled button component
│       ├── Card.tsx             # Glassmorphism card container
│       └── Select.tsx           # Styled dropdown
├── lib/
│   ├── api.ts                   # API client functions
│   ├── types.ts                 # TypeScript type definitions
│   └── utils.ts                 # Utility functions
├── hooks/
│   ├── useApi.ts               # API data fetching hooks
│   └── useJobPolling.ts        # Job status polling hook
└── public/
    └── (static assets)
```

---

## Step 1: Next.js Project Initialization

### 1.1 Initialize with create-next-app

```bash
cd /home/neonpulse/Dev/codezz/College/sem7/Qweave/mkdir -p qweave_ui
cd qweave_ui
npx create-next-app@14 . --typescript --tailwind --eslint --app --no-src-dir --import-alias="@/*" --use-npm
```

### 1.2 Install Dependencies

```bash
npm install @tanstack/react-query axios recharts lucide-react clsx tailwind-merge
```

---

## Step 2: Tailwind Configuration

**File:** `qweave_ui/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Quantum Synthetic Design System colors (from DESIGN.md)
      colors: {
        // Surface colors
        background: "#0b1326",
        surface: {
          DEFAULT: "#0b1326",
          dim: "#0b1326",
          bright: "#31394d",
          variant: "#2d3449",
        },
        "surface-container": {
          lowest: "#060e20",
          low: "#131b2e",
          DEFAULT: "#171f33",
          high: "#222a3d",
          highest: "#2d3449",
        },
        // Primary accent (Cyan)
        primary: {
          DEFAULT: "#8aebff",
          fixed: "#a2eeff",
          dim: "#2fd9f4",
          container: "#22d3ee",
        },
        // Secondary accent (Violet)
        secondary: {
          DEFAULT: "#d0bcff",
          fixed: "#e9ddff",
          dim: "#d0bcff",
          container: "#571bc1",
        },
        // Tertiary accent (Amber)
        tertiary: {
          DEFAULT: "#ffd6a3",
          fixed: "#ffddb5",
          dim: "#ffb957",
          container: "#ffb13b",
        },
        // Text colors
        "on-surface": "#dae2fd",
        "on-surface-variant": "#bbc9cd",
        "inverse-surface": "#dae2fd",
        "inverse-on-surface": "#283044",
        // Outline
        outline: {
          DEFAULT: "#859397",
          variant: "#3c494c",
        },
        // Error
        error: {
          DEFAULT: "#ffb4ab",
          container: "#93000a",
        },
        "on-primary": "#00363e",
        "on-primary-container": "#005763",
        "on-secondary": "#3c0091",
        "on-secondary-container": "#c4abff",
        "on-tertiary": "#462b00",
        "on-tertiary-container": "#6e4600",
        "on-error": "#690005",
        "on-error-container": "#ffdad6",
      },
      // Typography (Inter + JetBrains Mono)
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-md": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-sm": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "data-lg": ["20px", { lineHeight: "28px", fontWeight: "500" }],
        "data-md": ["14px", { lineHeight: "20px", fontWeight: "500" }],
        "label-caps": ["12px", { lineHeight: "16px", letterSpacing: "0.1em", fontWeight: "700" }],
      },
      // Spacing (4px base unit)
      spacing: {
        unit: "4px",
        gutter: "24px",
        margin: "32px",
        "container-padding": "20px",
      },
      // Border radius
      borderRadius: {
        sm: "0.125rem",
        DEFAULT: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
        full: "9999px",
      },
      // Backdrop blur for glassmorphism
      backdropBlur: {
        "2xl": "16px",
        "3xl": "24px",
      },
      // Box shadows for glow effects
      boxShadow: {
        glow: "0 0 15px rgba(47, 217, 244, 0.3)",
        "glow-strong": "0 0 25px rgba(47, 217, 244, 0.5)",
        "glow-secondary": "0 0 15px rgba(208, 188, 255, 0.3)",
        "glow-tertiary": "0 0 15px rgba(255, 214, 163, 0.3)",
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        dash: "dash 20s linear infinite",
      },
      keyframes: {
        dash: {
          to: { strokeDashoffset: "-100" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## Step 3: Global Styles

**File:** `qweave_ui/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=JetBrains+Mono:wght@100..800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* Reset and base styles */
@layer base {
  * {
    @apply border-outline-variant;
  }

  html, body {
    @apply m-0 p-0;
    overscroll-behavior: none;
  }

  body {
    @apply bg-background text-on-surface font-sans antialiased;
  }
}

/* Glassmorphism utility classes */
@layer components {
  .glass-panel {
    @apply bg-surface-container/60 backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/5;
  }

  .glass-card {
    @apply bg-surface-container/80 backdrop-blur-xl rounded-2xl shadow-md border border-white/5;
  }

  .glass-input {
    @apply bg-surface-variant text-on-surface font-mono text-data-md rounded-xl p-3 border border-outline-variant
           focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary;
  }

  /* Glow button variants */
  .btn-primary {
    @apply bg-primary text-on-primary font-mono text-label-caps uppercase tracking-widest rounded-xl
           px-6 py-3 transition-all duration-300
           hover:shadow-glow hover:shadow-glow-strong;
  }

  .btn-secondary {
    @apply bg-transparent border border-primary text-primary font-mono text-label-caps uppercase tracking-widest rounded-xl
           px-6 py-3 transition-all duration-300
           hover:bg-primary/10 hover:shadow-glow;
  }

  /* Data table styling */
  .data-table {
    @apply w-full text-right font-mono text-data-md border-collapse;
  }

  .data-table th {
    @apply p-3 text-on-surface-variant text-xs opacity-70 font-normal;
  }

  .data-table td {
    @apply p-3 text-on-surface;
  }

  .data-table tr:nth-child(odd) {
    @apply bg-white/[0.02];
  }

  .data-table tr:hover {
    @apply bg-white/[0.05];
  }
}

/* Material Symbols font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

/* Custom scrollbar hiding */
::-webkit-scrollbar {
  display: none;
}

/* Range input styling */
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: #2d3449;
  height: 4px;
  border-radius: 9999px;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: #22d3ee;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
}

input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #22d3ee;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
}
```

---

## Step 4: Type Definitions

**File:** `qweave_ui/lib/types.ts`

```typescript
/** Type definitions for Q-Weave API responses */

export enum NoiseTier {
  HIGH = "HIGH",
  MEDIUM = "MEDIUM",
  LOW = "LOW",
}

export enum BenchmarkType {
  GHZ = "GHZ",
  QFT = "QFT",
  QAOA = "QAOA",
  RANDOM_CLIFFORD = "RANDOM_CLIFFORD",
  VQE = "VQE",
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  message?: string;
  created_at: string;
  completed_at?: string;
}

export interface InteractionMatrix {
  characterization_id: string;
  labels: number[][];
  matrix: number[][];
  num_operations: number;
  noise_tier: string;
}

export interface GraphNode {
  id: number;
  label: string;
  qubits: number[];
}

export interface GraphEdge {
  source: number;
  target: number;
  weight: number;
}

export interface CrosstalkGraph {
  characterization_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  max_interaction: number;
}

export interface MitigationMetrics {
  original_depth: number;
  mitigated_depth: number;
  original_two_qubit_gates: number;
  mitigated_two_qubit_gates: number;
  depth_change: number;
  depth_change_percent: number;
  schedule_layers: number;
  qubit_mapping: Record<string, number>;
}

export interface MitigationResponse {
  mitigation_id: string;
  characterization_id: string;
  circuit_qasm: string;
  metrics: MitigationMetrics;
}

export interface ExecutionCounts {
  counts: Record<string, number>;
  shots: number;
}

export interface FidelityMetrics {
  baseline_fidelity: number;
  mitigated_fidelity: number;
  improvement: number;
  improvement_percent: number;
}

export interface EvaluationResponse {
  evaluation_id: string;
  baseline: ExecutionCounts;
  mitigated: ExecutionCounts;
  fidelity: FidelityMetrics;
  metrics: MitigationMetrics;
  noise_tier: string;
}

export interface BenchmarkCircuit {
  name: string;
  num_qubits: number;
  depth: number;
  num_nonlocal_gates: number;
  qasm: string;
}
```

---

## Step 5: API Client

**File:** `qweave_ui/lib/api.ts`

```typescript
/** API client for Q-Weave backend */

import axios from "axios";
import {
  JobStatus,
  InteractionMatrix,
  CrosstalkGraph,
  MitigationResponse,
  EvaluationResponse,
  BenchmarkCircuit,
  NoiseTier,
  BenchmarkType,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 300000, // 5 minute timeout for long-running operations
});

// Health check
export async function healthCheck() {
  const response = await api.get("/health");
  return response.data;
}

// Benchmark generation
export async function getBenchmark(
  type: BenchmarkType,
  numQubits: number,
  noiseTier: NoiseTier = NoiseTier.MEDIUM
): Promise<BenchmarkCircuit> {
  const response = await api.post("/api/benchmark", {
    benchmark_type: type,
    num_qubits: numQubits,
    noise_tier: noiseTier,
  });
  return response.data;
}

// Characterization
export async function startCharacterization(
  numQubits: number,
  noiseTier: NoiseTier,
  shots: number = 8192
): Promise<JobStatus> {
  const response = await api.post("/api/characterize", {
    circuit: {
      num_qubits: numQubits,
      name: "characterization_circuit",
    },
    noise_tier: noiseTier,
    shots,
  });
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get(`/api/characterize/${jobId}/status`);
  return response.data;
}

export async function getCharacterizationResult(
  jobId: string
): Promise<InteractionMatrix> {
  const response = await api.get(`/api/characterize/${jobId}/result`);
  return response.data;
}

// Graph
export async function getGraph(
  characterizationId: string
): Promise<CrosstalkGraph> {
  const response = await api.get(`/api/graph/${characterizationId}`);
  return response.data;
}

export async function getStrongestInteractions(
  characterizationId: string,
  limit: number = 10
) {
  const response = await api.get(
    `/api/graph/${characterizationId}/strongest?limit=${limit}`
  );
  return response.data;
}

// Mitigation
export async function startMitigation(
  characterizationId: string,
  circuitQasm: string,
  noiseTier: NoiseTier
): Promise<JobStatus> {
  const response = await api.post("/api/mitigate", {
    circuit: {
      qasm: circuitQasm,
      num_qubits: 4,
    },
    characterization_id: characterizationId,
    noise_tier: noiseTier,
  });
  return response.data;
}

export async function getMitigationStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get(`/api/mitigate/${jobId}/status`);
  return response.data;
}

export async function getMitigationResult(
  jobId: string
): Promise<MitigationResponse> {
  const response = await api.get(`/api/mitigate/${jobId}/result`);
  return response.data;
}

// Evaluation
export async function startEvaluation(
  mitigationId: string,
  circuitQasm: string,
  noiseTier: NoiseTier,
  shots: number = 8192
): Promise<JobStatus> {
  const response = await api.post("/api/evaluate", {
    circuit: {
      qasm: circuitQasm,
      num_qubits: 4,
    },
    mitigation_id: mitigationId,
    noise_tier: noiseTier,
    shots,
  });
  return response.data;
}

export async function getEvaluationStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get(`/api/evaluate/${jobId}/status`);
  return response.data;
}

export async function getEvaluationResult(
  jobId: string
): Promise<EvaluationResponse> {
  const response = await api.get(`/api/evaluate/${jobId}/result`);
  return response.data;
}
```

---

## Step 6: Root Layout

**File:** `qweave_ui/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Q-Weave Engine | Crosstalk-Aware Quantum Compiler",
  description:
    "Empirical framework for crosstalk-aware error mitigation in NISQ quantum circuits",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-on-surface overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
```

---

## Step 7: Sidebar Component

**File:** `qweave_ui/components/layout/Sidebar.tsx`

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  Cpu,
  Terminal,
  BarChart3,
  Play,
} from "lucide-react";
import { NoiseTier, BenchmarkType } from "@/lib/types";

const navItems = [
  { path: "/hardware", label: "Hardware", icon: Cpu },
  { path: "/compiler", label: "Compiler", icon: Terminal },
  { path: "/evaluation", label: "Evaluation", icon: BarChart3 },
];

interface SidebarProps {
  onRunMitigation?: () => void;
  isRunning?: boolean;
}

export default function Sidebar({ onRunMitigation, isRunning }: SidebarProps) {
  const pathname = usePathname();
  const [benchmark, setBenchmark] = useState<BenchmarkType>(BenchmarkType.GHZ);
  const [noiseSeverity, setNoiseSeverity] = useState<number>(45);

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-low border-r border-white/10 z-50 flex flex-col overflow-y-auto">
      {/* Logo */}
      <div className="p-6 mb-6">
        <div className="flex items-center gap-2 mb-8">
          <span className="material-symbols-outlined text-primary text-3xl">
            4k
          </span>
          <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight">
            Q-Weave
          </span>
        </div>

        {/* Controls */}
        <div className="space-y-6">
          {/* Benchmark Select */}
          <div className="flex flex-col gap-1">
            <label className="font-label-caps text-label-caps text-on-surface-variant uppercase">
              Benchmark Circuit
            </label>
            <select
              value={benchmark}
              onChange={(e) => setBenchmark(e.target.value as BenchmarkType)}
              className="glass-input w-full"
            >
              <option value={BenchmarkType.GHZ}>GHZ State</option>
              <option value={BenchmarkType.QAOA}>QAOA Solver</option>
              <option value={BenchmarkType.QFT}>QFT Transform</option>
              <option value={BenchmarkType.RANDOM_CLIFFORD}>
                Random Clifford
              </option>
              <option value={BenchmarkType.VQE}>VQE Circuit</option>
            </select>
          </div>

          {/* Noise Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center">
              <label className="font-label-caps text-label-caps text-on-surface-variant uppercase">
                Noise Severity
              </label>
              <span className="font-data-md text-data-md text-primary">
                {noiseSeverity}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={noiseSeverity}
              onChange={(e) => setNoiseSeverity(Number(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          {/* Run Button */}
          <button
            onClick={onRunMitigation}
            disabled={isRunning}
            className="w-full py-3 bg-primary text-on-primary font-label-caps text-label-caps rounded-xl
                       hover:shadow-glow transition-all flex items-center justify-center gap-2
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <span className="animate-spin">
                  <span className="material-symbols-outlined text-lg">refresh</span>
                </span>
                RUNNING...
              </>
            ) : (
              <>
                RUN MITIGATION
                <Play className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 border-t border-white/5 pt-6">
        <div className="px-4 mb-4 font-label-caps text-label-caps text-outline uppercase">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname?.startsWith(item.path);
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center px-4 py-3 rounded-xl transition-all mb-1
                ${
                  isActive
                    ? "bg-primary-container text-on-primary-container font-bold"
                    : "text-on-surface-variant hover:bg-surface-variant hover:text-on-surface"
                }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Version */}
      <div className="p-6 border-t border-white/5 text-center">
        <span className="font-label-caps text-[10px] text-outline-variant">
          CORE ENGINE V0.1.0-MVP
        </span>
      </div>
    </aside>
  );
}
```

---

## Step 8: Header Component

**File:** `qweave_ui/components/layout/Header.tsx`

```tsx
import { Settings, Bell, Search } from "lucide-react";

export default function Header() {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-background/80 backdrop-blur-xl border-b border-white/5 z-40 flex items-center justify-between px-6">
      {/* Left: Title + Status */}
      <div className="flex items-center gap-6">
        <span className="font-headline-sm text-headline-sm text-on-surface">
          Dashboard
        </span>
        <div className="flex items-center gap-4 bg-surface-container px-4 py-1.5 rounded-full border border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            <span className="font-data-md text-data-md text-on-surface">
              Quantum State: Active
            </span>
          </div>
          <div className="w-px h-4 bg-outline-variant"></div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-tertiary">
              ac_unit
            </span>
            <span className="font-data-md text-data-md text-on-surface">
              20mK
            </span>
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-6">
        <div className="flex gap-4">
          <Search className="w-5 h-5 text-on-surface-variant hover:text-primary cursor-pointer transition-colors" />
          <Bell className="w-5 h-5 text-on-surface-variant hover:text-primary cursor-pointer transition-colors" />
          <Settings className="w-5 h-5 text-on-surface-variant hover:text-primary cursor-pointer transition-colors" />
        </div>
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <span className="material-symbols-outlined text-on-primary text-lg">
            person
          </span>
        </div>
      </div>
    </header>
  );
}
```

---

## Step 9: Hardware Model Page (Tab 1)

**File:** `qweave_ui/app/hardware/page.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { getGraph, getStrongestInteractions } from "@/lib/api";
import { CrosstalkGraph, GraphEdge, GraphNode } from "@/lib/types";

export default function HardwarePage() {
  const [graph, setGraph] = useState<CrosstalkGraph | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data for initial render - replace with actual API call
  useEffect(() => {
    // In production, fetch from API:
    // const charId = "char_xxx";
    // const data = await getGraph(charId);
    // setGraph(data);

    // Mock data based on prototype
    setTimeout(() => {
      setGraph({
        characterization_id: "mock",
        nodes: [
          { id: 0, label: "CX(0,1)", qubits: [0, 1] },
          { id: 1, label: "CX(2,3)", qubits: [2, 3] },
          { id: 2, label: "CX(4,5)", qubits: [4, 5] },
          { id: 3, label: "CX(6,7)", qubits: [6, 7] },
          { id: 4, label: "CX(1,4)", qubits: [1, 4] },
        ],
        edges: [
          { source: 0, target: 1, weight: 0.9 },
          { source: 0, target: 4, weight: 0.08 },
          { source: 1, target: 2, weight: 0.05 },
          { source: 3, target: 4, weight: 0.12 },
        ],
        max_interaction: 0.9,
      });
      setLoading(false);
    }, 1000);
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 pl-72">
        <Header />
        <main className="pt-16 min-h-screen bg-background">
          <div className="flex flex-col w-full">
            {/* Sub-navigation */}
            <div className="flex items-center justify-between px-8 py-6 bg-surface-container-lowest shadow-sm z-10 relative">
              <div className="flex items-center gap-2 bg-surface-container p-1 rounded-xl shadow-inner">
                <button className="px-6 py-2 rounded-lg bg-primary/20 text-primary font-label-caps text-label-caps tracking-widest shadow-sm transition-all flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">share</span>
                  TOPOLOGY
                </button>
                <button className="px-6 py-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 font-label-caps text-label-caps tracking-widest transition-all flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">tune</span>
                  CALIBRATION
                </button>
                <button className="px-6 py-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 font-label-caps text-label-caps tracking-widest transition-all flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">memory</span>
                  ERROR RATES
                </button>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-secondary animate-pulse shadow-glow-secondary"></div>
                  <span className="font-data-md text-data-md text-on-surface-variant">
                    Live Telemetry
                  </span>
                </div>
                <button className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-on-surface hover:bg-primary hover:text-on-primary transition-all shadow-md">
                  <span className="material-symbols-outlined text-lg">refresh</span>
                </button>
              </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-12 gap-8 p-8 relative">
              {/* Background glows */}
              <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] pointer-events-none"></div>
              <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-secondary/5 rounded-full blur-[80px] pointer-events-none"></div>

              {/* Left: Network Graph */}
              <div className="col-span-12 xl:col-span-8 flex flex-col relative z-10">
                <div className="glass-panel p-6 h-[700px] flex flex-col relative overflow-hidden">
                  {/* Graph Header */}
                  <div className="flex items-start justify-between mb-4 relative z-10">
                    <div>
                      <h2 className="font-headline-md text-headline-md text-on-surface mb-2">
                        QPU Topology Map
                      </h2>
                      <p className="font-body-md text-body-md text-on-surface-variant max-w-md">
                        Real-time visualization of crosstalk interaction graph. Edge colors represent
                        interaction severity (Cyan: &lt;1%, Violet: &gt;5%).
                      </p>
                    </div>
                    <div className="flex flex-col gap-1 text-right">
                      <span className="font-label-caps text-label-caps text-primary">
                        GRAPH RESOLUTION: 4K
                      </span>
                      <span className="font-data-md text-data-md text-on-surface-variant">
                        LATTICE: 3x3 GRID
                      </span>
                    </div>
                  </div>

                  {/* Graph Visualization */}
                  <div className="flex-1 w-full relative bg-surface-container-lowest/30 rounded-2xl shadow-inner flex items-center justify-center overflow-hidden">
                    {/* Grid background */}
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_80%)] pointer-events-none"></div>

                    {/* SVG Graph */}
                    {loading ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                      </div>
                    ) : (
                      <NetworkGraph graph={graph!} />
                    )}

                    {/* Legend */}
                    <div className="absolute bottom-6 left-6 bg-surface-container-highest/80 backdrop-blur-md px-4 py-3 rounded-xl shadow-lg flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-1 bg-primary rounded-full"></div>
                        <span className="font-data-md text-data-md text-on-surface-variant text-xs">
                          Optimal
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-1 bg-gradient-to-r from-primary to-secondary rounded-full"></div>
                        <span className="font-data-md text-data-md text-on-surface-variant text-xs">
                          Moderate
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-1 bg-gradient-to-r from-secondary to-error rounded-full"></div>
                        <span className="font-data-md text-data-md text-on-surface-variant text-xs">
                          Critical
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: Stats + Matrix */}
              <div className="col-span-12 xl:col-span-4 flex flex-col gap-8 relative z-10">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-card p-5 hover:bg-surface-container-high transition-colors">
                    <p className="font-label-caps text-label-caps text-on-surface-variant mb-2">
                      GLOBAL COHERENCE
                    </p>
                    <div className="flex items-baseline gap-2">
                      <h3 className="font-display-lg text-4xl font-bold text-primary">98.4</h3>
                      <span className="font-data-md text-data-md text-primary-dim">%</span>
                    </div>
                  </div>
                  <div className="glass-card p-5 hover:bg-surface-container-high transition-colors">
                    <p className="font-label-caps text-label-caps text-on-surface-variant mb-2">
                      PEAK CROSSTALK
                    </p>
                    <div className="flex items-baseline gap-2">
                      <h3 className="font-display-lg text-4xl font-bold text-secondary">0.12</h3>
                      <span className="font-data-md text-data-md text-secondary-fixed-dim"></span>
                    </div>
                  </div>
                </div>

                {/* Interaction Matrix */}
                <div className="flex-1 glass-panel p-6 flex flex-col relative overflow-hidden">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-headline-sm text-headline-sm text-on-surface">
                      Interaction Matrix
                    </h3>
                    <button className="text-primary hover:text-primary-fixed transition-colors">
                      <span className="material-symbols-outlined text-lg">open_in_new</span>
                    </button>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface-variant mb-6 text-sm">
                    Estimated interaction strengths between concurrent operations. High values
                    indicate significant crosstalk effects.
                  </p>

                  {/* Matrix Table */}
                  <div className="flex-1 overflow-x-auto">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th className="text-left">NODE</th>
                          <th>G0</th>
                          <th>G1</th>
                          <th>G2</th>
                          <th>G3</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="rounded-xl group">
                          <td className="text-left text-primary font-bold">G0</td>
                          <td className="text-surface-variant">-</td>
                          <td>0.90</td>
                          <td>0.05</td>
                          <td>0.10</td>
                        </tr>
                        <tr className="group">
                          <td className="text-left text-primary font-bold">G1</td>
                          <td>0.90</td>
                          <td className="text-surface-variant">-</td>
                          <td>0.08</td>
                          <td>0.20</td>
                        </tr>
                        <tr className="group">
                          <td className="text-left text-primary font-bold">G2</td>
                          <td>0.05</td>
                          <td>0.08</td>
                          <td className="text-surface-variant">-</td>
                          <td>0.03</td>
                        </tr>
                        <tr className="bg-secondary/10 shadow-[inset_4px_0_0_0_#d0bcff] group">
                          <td className="text-left text-secondary font-bold">G3</td>
                          <td className="text-secondary">0.10</td>
                          <td className="text-secondary">0.20</td>
                          <td className="text-secondary">0.03</td>
                          <td className="text-surface-variant">-</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <button className="mt-6 w-full py-4 rounded-xl bg-transparent border border-secondary text-secondary font-label-caps text-label-caps tracking-widest hover:bg-secondary/10 hover:shadow-glow-secondary transition-all flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-lg">auto_fix_high</span>
                    VIEW FULL MATRIX
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// Network Graph Component
function NetworkGraph({ graph }: { graph: CrosstalkGraph }) {
  // Simple force-directed layout positions
  const positions: Record<number, { x: number; y: number }> = {
    0: { x: 400, y: 100 },
    1: { x: 250, y: 200 },
    2: { x: 550, y: 200 },
    3: { x: 400, y: 275 },
    4: { x: 250, y: 350 },
  };

  const getEdgeColor = (weight: number) => {
    if (weight > 0.5) return "url(#grad-critical)";
    if (weight > 0.2) return "url(#grad-warning)";
    return "url(#grad-stable)";
  };

  const getEdgeWidth = (weight: number) => {
    return 2 + weight * 4;
  };

  return (
    <svg className="w-full h-full drop-shadow-xl" viewBox="0 0 800 500">
      <defs>
        <filter id="glow" width="140%" height="140%" x="-20%" y="-20%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <linearGradient id="grad-stable" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#8aebff" />
          <stop offset="100%" stopColor="#2fd9f4" />
        </linearGradient>
        <linearGradient id="grad-warning" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#8aebff" />
          <stop offset="100%" stopColor="#d0bcff" />
        </linearGradient>
        <linearGradient id="grad-critical" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#d0bcff" />
          <stop offset="100%" stopColor="#ffb4ab" />
        </linearGradient>
      </defs>

      {/* Edges */}
      <g fill="none">
        {graph.edges.map((edge, i) => (
          <line
            key={i}
            x1={positions[edge.source]?.x || 0}
            y1={positions[edge.source]?.y || 0}
            x2={positions[edge.target]?.x || 0}
            y2={positions[edge.target]?.y || 0}
            stroke={getEdgeColor(edge.weight)}
            strokeWidth={getEdgeWidth(edge.weight)}
            opacity={0.7}
          />
        ))}
      </g>

      {/* Nodes */}
      <g className="font-mono text-data-md text-on-surface">
        {graph.nodes.map((node) => {
          const pos = positions[node.id] || { x: 0, y: 0 };
          const isHighCrosstalk = graph.edges.some(
            (e) =>
              (e.source === node.id || e.target === node.id) && e.weight > 0.08
          );

          return (
            <g
              key={node.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              className="cursor-pointer hover:scale-110 transition-transform origin-center"
            >
              {isHighCrosstalk && (
                <circle
                  r="32"
                  fill="currentColor"
                  className="text-secondary/40 animate-ping"
                />
              )}
              <circle
                r="24"
                fill="currentColor"
                className={isHighCrosstalk ? "text-secondary" : "text-surface-bright"}
                filter="url(#glow)"
              />
              <circle
                r="20"
                fill="currentColor"
                className="text-surface-container"
              />
              <text
                textAnchor="middle"
                dominantBaseline="central"
                className={isHighCrosstalk ? "fill-secondary-fixed font-bold" : "fill-on-surface"}
              >
                {node.label.slice(0, 4)}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}
```

---

## Step 10: Compiler Page (Tab 2)

**File:** `qweave_ui/app/compiler/page.tsx`

```tsx
"use client";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { ArrowDown, Download, Layers } from "lucide-react";

export default function CompilerPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 pl-72">
        <Header />
        <main className="pt-16 min-h-screen bg-background">
          <div className="flex flex-col w-full h-full relative">
            {/* Background glow */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/5 via-background/20 to-transparent pointer-events-none z-0"></div>

            <div className="relative z-10 flex flex-col h-full gap-6 p-5">
              {/* Header */}
              <header className="flex justify-between items-end pb-4 border-b border-outline-variant/30">
                <div>
                  <h1 className="font-display-lg text-display-lg text-on-surface mb-2">
                    Compiler Pass Comparison
                  </h1>
                  <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
                    Visualizing schedule differences between the standard Qiskit transpiler and
                    the Q-Weave mitigated pipeline.
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex flex-col items-end">
                    <span className="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">
                      Gate Depth Change
                    </span>
                    <span className="font-headline-md text-headline-md text-primary">+3.2%</span>
                  </div>
                  <div className="h-10 w-px bg-outline-variant/50"></div>
                  <div className="flex flex-col items-end">
                    <span className="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">
                      Est. Fidelity Gain
                    </span>
                    <span className="font-headline-md text-headline-md text-tertiary">+12.7%</span>
                  </div>
                </div>
              </header>

              {/* Comparison Grid */}
              <div className="grid grid-cols-2 gap-6 flex-1 min-h-0">
                {/* Standard Schedule */}
                <section className="flex flex-col h-full glass-card shadow-lg overflow-hidden">
                  <div className="bg-surface-container/60 p-4 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Layers className="w-5 h-5 text-outline" />
                      <h2 className="font-headline-sm text-headline-sm text-on-surface">
                        Standard Schedule
                      </h2>
                    </div>
                    <span className="font-label-caps text-label-caps text-on-surface-variant bg-surface-variant/50 px-2 py-1 rounded">
                      Base Qiskit
                    </span>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    <GateBlock
                      tick={0}
                      time="12.5ns"
                      gates={["RZ(π/2) q[0]", "H q[1]", "CX q[0], q[1]", "Barrier"]}
                    />
                    <GateBlock
                      tick={1}
                      time="45.0ns"
                      gates={["RZ(π/4) q[2]", "CX q[1], q[2]", "T q[0]"]}
                    />
                    <GateBlock
                      tick={2}
                      time="78.2ns"
                      gates={["CX q[2], q[3]", "RZ(-π/4) q[1]", "S q[0]"]}
                    />
                    <GateBlock tick={3} time="115.0ns" gates={["Measure q[0..3]"]} />
                  </div>
                </section>

                {/* Mitigated Schedule */}
                <section className="flex flex-col h-full glass-card shadow-xl border border-primary/20 overflow-hidden relative">
                  <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none"></div>
                  <div className="bg-surface-container-high/80 p-4 border-b border-primary/20 flex items-center justify-between relative z-10 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-primary shadow-glow">
                        auto_fix_high
                      </span>
                      <h2 className="font-headline-sm text-headline-sm text-primary">
                        Q-Weave Mitigated
                      </h2>
                    </div>
                    <div className="flex items-center gap-2 bg-primary/10 px-3 py-1.5 rounded-full border border-primary/30">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                      <span className="font-label-caps text-label-caps text-primary uppercase">
                        Optimized
                      </span>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
                    <MitigatedGateBlock
                      tick={0}
                      time="12.5ns"
                      gates={[
                        { text: "U3(π/2, 0, π) q[0]", highlight: false, note: "// RZ + H folded" },
                        { text: "ECR q[0], q[1]", highlight: true, note: "// Echoed CR" },
                        { text: "Barrier", highlight: false },
                      ]}
                      badge="MERGED"
                    />
                    <MitigatedGateBlock
                      tick={1}
                      time="42.8ns"
                      gates={[
                        { text: "RZ(π/4) q[2]", highlight: false },
                        { text: "DD q[0]", highlight: "primary", note: "// Dynamical Decoupling" },
                        { text: "ECR q[1], q[2]", highlight: false },
                        { text: "T q[0]", highlight: "primary", note: "// Scheduled early" },
                      ]}
                      badge="SHIFTED"
                      shifted
                    />
                    <MitigatedGateBlock
                      tick={2}
                      time="74.0ns"
                      gates={[
                        { text: "ECR q[2], q[3]", highlight: false },
                        { text: "RZ(-π/4) q[1]", highlight: false },
                        { text: "DD q[0]", highlight: "primary", note: "// Idle suppression" },
                      ]}
                    />
                    <MitigatedGateBlock
                      tick={3}
                      time="102.5ns"
                      gates={[{ text: "MeasureMitigated q[0..3]", highlight: "secondary" }]}
                      badge="RO-MITIGATED"
                    />
                  </div>
                </section>
              </div>

              {/* Footer Context Bar */}
              <div className="mt-4 bg-surface-container/50 backdrop-blur-md rounded-xl p-3 border border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="font-label-caps text-label-caps text-outline-variant uppercase">
                    Key:
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary shadow-glow"></div>
                    <span className="font-data-md text-data-md text-on-surface-variant">
                      Relocated/Inserted
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-tertiary shadow-glow-tertiary"></div>
                    <span className="font-data-md text-data-md text-on-surface-variant">
                      Merged Ops
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-secondary shadow-glow-secondary"></div>
                    <span className="font-data-md text-data-md text-on-surface-variant">
                      Measurement Mod
                    </span>
                  </div>
                </div>
                <button className="px-4 py-2 bg-surface-container-high border border-outline/30 rounded-lg hover:border-primary/50 transition-colors font-label-caps text-label-caps text-on-surface flex items-center gap-2">
                  Export Diff <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// Standard Gate Block
function GateBlock({
  tick,
  time,
  gates,
}: {
  tick: number;
  time: string;
  gates: string[];
}) {
  return (
    <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/20 shadow-sm relative group transition-all duration-300 hover:border-outline/50">
      <div className="flex justify-between items-center mb-3">
        <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">
          Tick {tick}
        </span>
        <span className="font-data-md text-data-md text-on-surface-variant opacity-50">
          {time}
        </span>
      </div>
      <pre className="font-mono text-data-md text-on-surface bg-background/50 p-3 rounded-lg overflow-x-auto">
        {gates.join("\n")}
      </pre>
    </div>
  );
}

// Mitigated Gate Block
function MitigatedGateBlock({
  tick,
  time,
  gates,
  badge,
  shifted,
}: {
  tick: number;
  time: string;
  gates: { text: string; highlight?: boolean | string; note?: string }[];
  badge?: string;
  shifted?: boolean;
}) {
  const getBadgeColor = () => {
    switch (badge) {
      case "MERGED":
        return "bg-tertiary/10 text-tertiary border-tertiary/20";
      case "SHIFTED":
        return "bg-primary/10 text-primary border-primary/20";
      case "RO-MITIGATED":
        return "bg-secondary/10 text-secondary border-secondary/20";
      default:
        return "bg-surface-variant text-on-surface-variant";
    }
  };

  return (
    <div
      className={`bg-surface-container rounded-xl p-4 border border-outline-variant/30 shadow-md relative group transition-all duration-300 hover:border-primary/50
        ${shifted ? "bg-gradient-to-r from-surface-container via-surface-container to-primary/5" : ""}`}
    >
      <div className="flex justify-between items-center mb-3">
        <span className="font-label-caps text-label-caps text-primary uppercase tracking-wider flex items-center gap-2">
          <ArrowDown className="w-4 h-4" /> Tick {tick}
        </span>
        <div className="flex items-center gap-2">
          {badge && (
            <span
              className={`font-label-caps text-label-caps px-1.5 py-0.5 rounded border ${getBadgeColor()}`}
            >
              {badge}
            </span>
          )}
          <span className="font-data-md text-data-md text-primary opacity-80">{time}</span>
        </div>
      </div>
      <pre className="font-mono text-data-md text-on-surface bg-surface-container-low p-3 rounded-lg overflow-x-auto">
        {gates.map((gate, i) => (
          <div key={i}>
            <code
              className={`
              ${gate.highlight === true || gate.highlight === "primary" ? "text-primary font-bold shadow-[0_0_8px_rgba(47,217,244,0.3)] bg-primary/10 px-1 rounded" : ""}
              ${gate.highlight === "secondary" ? "text-secondary font-bold bg-secondary/10 px-1 rounded" : ""}
              ${!gate.highlight ? "text-on-surface-variant" : ""}
            `}
            >
              {gate.text}
            </code>
            {gate.note && (
              <span className="text-primary opacity-70 ml-2 text-xs italic">{gate.note}</span>
            )}
          </div>
        ))}
      </pre>
    </div>
  );
}
```

---

## Step 11: Evaluation Page (Tab 3)

**File:** `qweave_ui/app/evaluation/page.tsx`

```tsx
"use client";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { TrendingUp, CheckCircle2, Layers, Cpu } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Mock data for bar chart
const chartData = [
  { name: "GHZ State", raw: 0.45, mitigated: 0.82 },
  { name: "QAOA Solver", raw: 0.32, mitigated: 0.68 },
  { name: "QFT Transform", raw: 0.18, mitigated: 0.55 },
  { name: "Random Clifford", raw: 0.52, mitigated: 0.89 },
];

export default function EvaluationPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 pl-72">
        <Header />
        <main className="pt-16 min-h-screen bg-background">
          <div className="flex flex-col w-full px-6 pb-8">
            {/* Page Header */}
            <div className="flex justify-between items-end mb-6 py-4">
              <div className="flex flex-col gap-1">
                <h2 className="font-headline-md text-headline-md text-on-surface">
                  Evaluation Metrics
                </h2>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Real-time telemetry and post-mitigation performance analysis.
                </p>
              </div>
              <div className="flex items-center gap-2 font-mono text-data-md text-primary bg-primary/10 px-4 py-2 rounded-full border border-primary/20 backdrop-blur-md">
                <span className="w-2 h-2 rounded-full bg-primary shadow-glow animate-pulse"></span>
                LIVE FEED
              </div>
            </div>

            {/* Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Execution Fidelity */}
              <MetricCard
                icon={<CheckCircle2 className="w-4 h-4" />}
                label="Execution Fidelity"
                value="94.2"
                unit="%"
                trend="+2.4% vs unmitigated"
                trendUp
                color="primary"
              />

              {/* Circuit Depth */}
              <MetricCard
                icon={<Layers className="w-4 h-4" />}
                label="Circuit Depth"
                value="128"
                subtext="Optimized layers"
                color="secondary"
              />

              {/* 2-Qubit Gates */}
              <MetricCard
                icon={<Cpu className="w-4 h-4" />}
                label="2-Qubit Gate Count"
                value="456"
                subtext="Total operations"
                color="tertiary"
              />
            </div>

            {/* Bar Chart */}
            <div className="glass-panel p-8 shadow-xl border border-white/5 flex-1 flex flex-col relative overflow-hidden min-h-[500px]">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-surface-container-lowest/50 pointer-events-none"></div>

              <div className="flex justify-between items-start mb-8 relative z-10">
                <div className="flex flex-col gap-2">
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">
                    Execution Success Probability (ESP)
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
                    Comparative analysis of raw versus error-mitigated circuit execution across
                    standard quantum benchmark sets.
                  </p>
                </div>
                <div className="flex gap-6 font-mono text-data-md">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm bg-surface-variant border border-outline"></div>
                    <span className="text-on-surface-variant">Raw</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm bg-primary border border-primary-fixed"></div>
                    <span className="text-on-surface">Mitigated</span>
                  </div>
                </div>
              </div>

              {/* Recharts Bar Chart */}
              <div className="flex-1 relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{ top: 40, right: 30, left: 20, bottom: 20 }}
                    barGap={8}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(133, 147, 151, 0.2)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      axisLine={{ stroke: "rgba(133, 147, 151, 0.3)" }}
                      tickLine={false}
                      tick={{ fill: "#dae2fd", fontSize: 12, fontFamily: "JetBrains Mono" }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "rgba(133, 147, 151, 0.7)", fontSize: 12 }}
                      tickFormatter={(value) => value.toFixed(2)}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#171f33",
                        border: "1px solid rgba(133, 147, 151, 0.3)",
                        borderRadius: "8px",
                        fontFamily: "JetBrains Mono",
                      }}
                      labelStyle={{ color: "#dae2fd" }}
                      itemStyle={{ color: "#dae2fd" }}
                    />
                    <Bar
                      dataKey="raw"
                      fill="#2d3449"
                      stroke="#859397"
                      strokeWidth={1}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={60}
                      name="Raw"
                    />
                    <Bar
                      dataKey="mitigated"
                      fill="#8aebff"
                      stroke="#22d3ee"
                      strokeWidth={1}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={60}
                      name="Mitigated"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// Metric Card Component
function MetricCard({
  icon,
  label,
  value,
  unit,
  subtext,
  trend,
  trendUp,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  unit?: string;
  subtext?: string;
  trend?: string;
  trendUp?: boolean;
  color: "primary" | "secondary" | "tertiary";
}) {
  const colorClasses = {
    primary: "text-primary",
    secondary: "text-secondary",
    tertiary: "text-tertiary",
  };

  const bgClasses = {
    primary: "bg-primary/10",
    secondary: "bg-secondary/10",
    tertiary: "bg-tertiary/10",
  };

  const glowClasses = {
    primary: "group-hover:bg-primary/20 group-hover:shadow-glow",
    secondary: "group-hover:bg-secondary/20 group-hover:shadow-glow-secondary",
    tertiary: "group-hover:bg-tertiary/20 group-hover:shadow-glow-tertiary",
  };

  return (
    <div
      className={`glass-card relative overflow-hidden group hover:border-${color}/30 transition-colors duration-300`}
    >
      <div
        className={`absolute -right-12 -top-12 w-32 h-32 rounded-full blur-2xl transition-all duration-500 ${bgClasses[color]} ${glowClasses[color]}`}
      ></div>

      <div className="relative z-10 flex flex-col justify-between h-full gap-4 p-6">
        <div className="flex items-center justify-between">
          <span
            className={`font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider flex items-center gap-2`}
          >
            <span className={colorClasses[color]}>{icon}</span>
            {label}
          </span>
          <span className="material-symbols-outlined text-outline-variant text-lg">info</span>
        </div>

        <div className="flex items-baseline gap-2">
          <span className={`font-display-lg text-display-lg text-on-surface ${colorClasses[color]}`}>
            {value}
          </span>
          {unit && (
            <span className={`font-data-lg text-data-lg ${colorClasses[color]}-dim`}>{unit}</span>
          )}
        </div>

        {trend && (
          <div
            className={`flex items-center gap-2 font-data-md text-data-md ${trendUp ? "text-tertiary" : "text-error"}`}
          >
            <TrendingUp className={`w-4 h-4 ${trendUp ? "" : "rotate-180"}`} />
            {trend}
          </div>
        )}

        {subtext && <div className="font-data-md text-data-md text-on-surface-variant">{subtext}</div>}
      </div>
    </div>
  );
}
```

---

## Step 12: React Query Provider

**File:** `qweave_ui/app/providers.tsx`

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 2,
          },
        },
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

---

## Step 13: Update Root Layout with Providers

**File:** `qweave_ui/app/layout.tsx` (updated)

```tsx
import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Q-Weave Engine | Crosstalk-Aware Quantum Compiler",
  description:
    "Empirical framework for crosstalk-aware error mitigation in NISQ quantum circuits",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-on-surface antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

---

## Step 14: Environment Configuration

**File:** `qweave_ui/.env.local`

```bash
# Q-Weave Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Phase 4 Completion Criteria

**This phase is complete when:**

1. Next.js 14+ project initializes with TypeScript and Tailwind CSS
2. Quantum Synthetic design system is properly configured in `tailwind.config.ts`
3. Global styles in `globals.css` implement glassmorphism and custom components
4. All three dashboard tabs render correctly:
   - **Hardware (Tab 1)**: Interactive network graph, interaction matrix, stats cards
   - **Compiler (Tab 2)**: Side-by-side schedule panels, gate blocks, diff legend
   - **Evaluation (Tab 3)**: Metric cards, Recharts bar chart for success probability
5. Sidebar navigation with benchmark selector and noise severity slider
6. API client functions fetch data from FastAPI endpoints
7. React Query manages server state and caching
8. UI matches the Google Stitch prototype design (deep slate, neon cyan accents, glass panels)

---

## Running the Frontend

```bash
cd /home/neonpulse/Dev/codezz/College/sem7/Qweave/# Ensure backend is running first
cd qweave_ui
npm install
npm run dev
```

Access at: `http://localhost:3000`

---

## Frontend-Bakend Integration

The frontend communicates with the API at the following endpoints:

| Frontend Action | API Endpoint | Purpose |
|-----------------|--------------|---------|
| Select benchmark | `POST /api/benchmark` | Get circuit QASM |
| Click "Run Mitigation" | `POST /api/characterize` | Start characterization |
| Display graph | `GET /api/graph/{char_id}` | Get nodes/edges |
| View schedule | `GET /api/mitigate/{mit_id}/schedule` | Get layer schedule |
| Show metrics | `GET /api/evaluate/{eval_id}/result` | Get fidelity comparison |

---

## Next Phase

Proceed to [05_documentation_and_deliverables.md](./05_documentation_and_deliverables.md) to create documentation, benchmark scripts, and panel defense materials.
