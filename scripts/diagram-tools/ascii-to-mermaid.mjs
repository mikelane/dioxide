#!/usr/bin/env node
/**
 * Convert remaining ASCII diagrams to Mermaid SVGs.
 */

import { renderMermaid } from 'beautiful-mermaid';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = join(__dirname, '../../docs/_static/images/diagrams');

// Catppuccin Mocha theme
const THEME = {
  bg: '#1e1e2e',
  fg: '#cdd6f4',
  line: '#89b4fa',
  accent: '#89b4fa',
  muted: '#a6adc8',
  surface: '#313244',
  border: '#f5c2e7',
};

const diagrams = [
  {
    name: 'golden-path.svg',
    code: `flowchart TB
    subgraph core["@service (Core Domain)"]
        US["UserService<br/>(business logic)"]
    end

    subgraph port["Port (Protocol)"]
        EP["EmailPort"]
    end

    subgraph adapters["@adapter.for_(Port, profile=...)"]
        A1["SendGrid<br/>PRODUCTION"]
        A2["FakeEmail<br/>TEST"]
        A3["ConsoleEmail<br/>DEVELOPMENT"]
    end

    core -->|"depends on"| port
    port -->|"implemented by"| adapters`,
  },
  {
    name: 'decision-tree.svg',
    code: `flowchart TD
    A{{"Need to swap implementations<br/>based on profile?"}}
    A -->|YES| B["Define Port + @adapter.for_()"]
    A -->|NO| C{{"Core business logic?"}}
    C -->|YES| D["Use @service"]
    C -->|NO| E{{"Talks to external systems?"}}
    E -->|YES| B
    E -->|NO| D

    style B fill:#fab387
    style D fill:#89b4fa`,
  },
];

async function main() {
  console.log('Converting ASCII diagrams to SVG...\n');

  for (const diagram of diagrams) {
    const outputPath = join(OUTPUT_DIR, diagram.name);
    try {
      console.log(`  Rendering ${diagram.name}...`);
      const svg = await renderMermaid(diagram.code, THEME);
      writeFileSync(outputPath, svg);
      console.log(`  Saved ${diagram.name}`);
    } catch (error) {
      console.error(`  Failed: ${error.message}`);
    }
  }

  console.log('\nDone! Update docs to reference these SVGs.');
}

main().catch(console.error);
