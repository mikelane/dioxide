#!/usr/bin/env node
/**
 * Update documentation files to use SVG images instead of Mermaid code blocks.
 *
 * Usage: node update-docs.mjs
 *
 * This script reads the mappings.json and updates each documentation file
 * to replace Mermaid code blocks with image references.
 */

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = join(__dirname, '../../docs');
const DIAGRAMS_DIR = join(DOCS_DIR, '_static/images/diagrams');

// Read the mappings
const mappings = JSON.parse(readFileSync(join(DIAGRAMS_DIR, 'mappings.json'), 'utf-8'));

// Calculate relative path from doc file to diagrams
function getRelativeImagePath(docPath, imagePath) {
  // imagePath is like /_static/images/diagrams/foo.svg
  // We need relative path from the doc file location
  const docDir = dirname(join(DOCS_DIR, docPath));
  const imageFullPath = join(DOCS_DIR, imagePath.replace(/^\//, ''));
  return relative(docDir, imageFullPath);
}

// Extract alt text from Mermaid code
function extractAltText(mermaidCode) {
  // Try to find a meaningful description
  const subgraphMatch = mermaidCode.match(/subgraph\s+\w+\[["']?([^"'\]]+)/);
  if (subgraphMatch) {
    return subgraphMatch[1];
  }

  // Fall back to diagram type
  if (mermaidCode.includes('sequenceDiagram')) return 'Sequence diagram';
  if (mermaidCode.includes('flowchart')) return 'Flowchart diagram';
  if (mermaidCode.includes('classDiagram')) return 'Class diagram';
  if (mermaidCode.includes('stateDiagram')) return 'State diagram';

  return 'Architecture diagram';
}

// Process each file
for (const [docPath, diagrams] of Object.entries(mappings)) {
  const fullPath = join(DOCS_DIR, docPath);
  let content = readFileSync(fullPath, 'utf-8');

  console.log(`Processing ${docPath}...`);

  // Replace each Mermaid block with an image reference
  // Process in reverse order to maintain correct positions
  for (const diagram of diagrams.reverse()) {
    const relativePath = getRelativeImagePath(docPath, diagram.imagePath);
    const altText = extractAltText(diagram.original);

    // MyST Markdown image syntax
    const imageRef = `\`\`\`{image} ${relativePath}
:alt: ${altText}
:align: center
:class: diagram
\`\`\``;

    content = content.replace(diagram.original, imageRef);
    console.log(`  Replaced diagram ${diagram.index}: ${altText}`);
  }

  writeFileSync(fullPath, content);
  console.log(`  Saved ${docPath}`);
}

console.log('\nDone! All documentation files updated.');
