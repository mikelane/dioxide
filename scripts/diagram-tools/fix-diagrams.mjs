#!/usr/bin/env node
/**
 * Regenerate diagrams with fixed text (no <br/> tags).
 * Beautiful-mermaid renders <br/> literally instead of as line breaks.
 */

import { renderMermaid } from 'beautiful-mermaid';
import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = join(__dirname, '../../docs/_static/images/diagrams');

// Catppuccin Mocha theme - higher contrast
const THEME = {
  bg: '#1e1e2e',
  fg: '#cdd6f4',
  line: '#89b4fa',
  accent: '#89b4fa',
  muted: '#bac2de',  // Lighter muted for better readability
  surface: '#313244',
  border: '#f5c2e7',
};

// Fixed diagrams - dark text on light backgrounds for contrast
const diagrams = [
  // Decision tree - simplified with dark text on colored nodes
  {
    name: 'decision-tree.svg',
    code: `flowchart TD
    A{{"Swap implementations per profile?"}}
    A -->|YES| B["Port + @adapter.for_()"]
    A -->|NO| C{{"Core business logic?"}}
    C -->|YES| D["@service"]
    C -->|NO| E{{"Talks to external systems?"}}
    E -->|YES| B
    E -->|NO| D

    style B fill:#fab387,color:#1e1e2e
    style D fill:#89b4fa,color:#1e1e2e`,
  },

  // Golden path - cleaner labels
  {
    name: 'golden-path.svg',
    code: `flowchart TB
    subgraph core["@service - Core Domain"]
        US["UserService"]
    end

    subgraph port["Port - Protocol"]
        EP["EmailPort"]
    end

    subgraph adapters["@adapter.for_()"]
        A1["SendGrid - PROD"]
        A2["FakeEmail - TEST"]
        A3["Console - DEV"]
    end

    core -->|depends on| port
    port -->|implemented by| adapters`,
  },

  // Scoping diagram 0 - container overview with dark text
  {
    name: 'guides-scoping-0-container-applicatio.svg',
    code: `flowchart TB
    subgraph Container["Container - Application Lifetime"]
        S1[("UserService - singleton")]
        S2[("EmailService - singleton")]

        subgraph Scope1["Scope 1 - Request A"]
            R1A["RequestContext"]
            R1B["AuditLogger"]
        end

        subgraph Scope2["Scope 2 - Request B"]
            R2A["RequestContext"]
            R2B["AuditLogger"]
        end

        S1 --> R1A
        S1 --> R2A
        S2 --> R1A
        S2 --> R2A
    end

    style S1 fill:#89b4fa,color:#1e1e2e
    style S2 fill:#89b4fa,color:#1e1e2e
    style R1A fill:#fab387,color:#1e1e2e
    style R1B fill:#fab387,color:#1e1e2e
    style R2A fill:#fab387,color:#1e1e2e
    style R2B fill:#fab387,color:#1e1e2e`,
  },

  // Scoping diagram 2 - singleton vs scoped (was missing, had bad contrast)
  {
    name: 'guides-scoping-2-singleton-shared-.svg',
    code: `flowchart LR
    subgraph Singleton["Singleton - Shared"]
        US["UserService"]
        ES["EmailService"]
    end

    subgraph Scoped["Request-Scoped"]
        RC["RequestContext"]
        DB["DatabaseSession"]
        AL["AuditLogger"]
    end

    US --> RC
    US --> DB
    US --> AL

    style US fill:#89b4fa,color:#1e1e2e
    style ES fill:#89b4fa,color:#1e1e2e
    style RC fill:#fab387,color:#1e1e2e
    style DB fill:#fab387,color:#1e1e2e
    style AL fill:#fab387,color:#1e1e2e`,
  },

  // Scoping diagram 3 - parent container with dark text
  {
    name: 'guides-scoping-3-parent-container.svg',
    code: `flowchart TB
    subgraph Parent["Parent Container"]
        direction TB
        PS1["ConfigService - singleton"]
        PS2["UserService - singleton"]
    end

    subgraph Child["Scoped Container"]
        direction TB
        CS1["DatabaseSession - scoped"]
        CS2["RequestContext - scoped"]
    end

    Child -->|inherits from| Parent
    CS1 -->|depends on| PS1
    PS2 -->|injected with| CS1

    style PS1 fill:#89b4fa,color:#1e1e2e
    style PS2 fill:#89b4fa,color:#1e1e2e
    style CS1 fill:#fab387,color:#1e1e2e
    style CS2 fill:#fab387,color:#1e1e2e`,
  },

  // Scoping diagram 5 - flowchart decision with dark text
  {
    name: 'guides-scoping-5-flowchart.svg',
    code: `flowchart TD
    A[New Component] --> B{Core business logic?}
    B -->|Yes| C["@service SINGLETON"]
    B -->|No| D{Holds per-request state?}
    D -->|No| E{Needs per-request resources?}
    D -->|Yes| F["Scope.REQUEST"]
    E -->|No| G["SINGLETON default"]
    E -->|Yes| F

    style C fill:#89b4fa,color:#1e1e2e
    style G fill:#89b4fa,color:#1e1e2e
    style F fill:#fab387,color:#1e1e2e`,
  },

  // MLP Vision - architecture layers
  {
    name: 'MLP_VISION-0--service-core-domain.svg',
    code: `flowchart TB
    subgraph services["@service - Core Domain Logic"]
        direction TB
        S1["UserService"]
        S2["OrderService"]
    end

    subgraph ports["Ports - Protocols/ABCs"]
        direction TB
        P1["EmailPort"]
        P2["UserRepository"]
    end

    subgraph adapters["@adapter.for_()"]
        direction TB
        A1["SendGridAdapter"]
        A2["FakeEmailAdapter"]
    end

    services -->|depends on| ports
    ports -->|implemented by| adapters

    note1["Business rules, Profile-agnostic"]
    note2["Interfaces/contracts"]
    note3["Boundary implementations"]

    services ~~~ note1
    ports ~~~ note2
    adapters ~~~ note3`,
  },

  // Hexagonal architecture
  {
    name: 'user_guide-hexagonal_architecture-0--service-core-domain.svg',
    code: `flowchart TB
    subgraph services["@service - Core Domain Logic"]
        direction TB
        US[UserService]
        OS[OrderService]
        NS[NotificationService]
    end

    subgraph ports["Ports - Protocols/ABCs"]
        direction TB
        EP[EmailPort]
        UR[UserRepository]
        PG[PaymentGateway]
    end

    subgraph adapters["@adapter.for_()"]
        direction TB
        SG["SendGridAdapter - PROD"]
        FE["FakeEmailAdapter - TEST"]
        CE["ConsoleEmailAdapter - DEV"]
    end

    services -->|depends on| ports
    ports -->|implemented by| adapters`,
  },

  // Services vs adapters - mental model
  {
    name: 'user_guide-services-vs-adapters-0-external-world-br-dr.svg',
    code: `flowchart LR
    subgraph driving["Driving Side"]
        direction TB
        FA[FastAPI]
        CL[Click]
        FL[Flask]
    end

    subgraph core["Application Core"]
        direction TB
        SVC["@service"]
    end

    subgraph driven["Driven Side"]
        direction TB
        PORT["Port - Protocol"]
        ADP["@adapter"]
    end

    driving -->|calls| core
    core -->|depends on| PORT
    PORT -->|implemented by| ADP`,
  },
];

async function main() {
  console.log('Regenerating diagrams with fixed text...\n');

  for (const diagram of diagrams) {
    const outputPath = join(OUTPUT_DIR, diagram.name);
    try {
      console.log(`  Rendering ${diagram.name}...`);
      const svg = await renderMermaid(diagram.code, THEME);
      writeFileSync(outputPath, svg);
      console.log(`  ✓ Saved ${diagram.name}`);
    } catch (error) {
      console.error(`  ✗ Failed: ${error.message}`);
    }
  }

  console.log('\nDone!');
}

main().catch(console.error);
