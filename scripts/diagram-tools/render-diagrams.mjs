#!/usr/bin/env node
/**
 * Render Mermaid diagrams from documentation files as beautiful SVGs.
 *
 * Usage: node render-diagrams.mjs
 *
 * This script:
 * 1. Finds all Mermaid code blocks in docs/
 * 2. Renders each as an SVG using beautiful-mermaid
 * 3. Saves SVGs to docs/_static/images/diagrams/
 * 4. Outputs a mapping for updating the documentation
 */

import { renderMermaid } from 'beautiful-mermaid';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = join(__dirname, '../../docs');
const OUTPUT_DIR = join(DOCS_DIR, '_static/images/diagrams');

// Catppuccin Mocha theme - professional dark theme
const THEME = {
  bg: '#1e1e2e',      // Base background
  fg: '#cdd6f4',      // Text color
  line: '#89b4fa',    // Bright blue for edges (high contrast)
  accent: '#89b4fa',  // Arrow heads
  muted: '#a6adc8',   // Secondary text
  surface: '#313244', // Node fill
  border: '#f5c2e7',  // Node borders (pink/mauve)
};

// Find all markdown files recursively
function findMarkdownFiles(dir) {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('_') && entry.name !== 'api') {
      files.push(...findMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  return files;
}

// Extract Mermaid code blocks from a file
function extractMermaidBlocks(content, filePath) {
  const blocks = [];
  // Match ```{mermaid} or ```mermaid blocks
  const regex = /```\{?mermaid\}?\n([\s\S]*?)```/g;
  let match;
  let index = 0;

  while ((match = regex.exec(content)) !== null) {
    blocks.push({
      code: match[1].trim(),
      fullMatch: match[0],
      index: index++,
      filePath,
    });
  }
  return blocks;
}

// Generate a filename from the file path and diagram index
function generateFilename(filePath, index, code) {
  const relativePath = filePath.replace(DOCS_DIR + '/', '').replace(/\//g, '-').replace('.md', '');
  // Try to extract a meaningful name from the diagram
  const subgraphMatch = code.match(/subgraph\s+\w+\[["']?([^"'\]]+)/);
  const graphTypeMatch = code.match(/^(flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram)/m);

  let suffix = '';
  if (subgraphMatch) {
    suffix = '-' + subgraphMatch[1].toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 20);
  } else if (graphTypeMatch) {
    suffix = '-' + graphTypeMatch[1].toLowerCase().replace('diagram', '');
  }

  return `${relativePath}-${index}${suffix}.svg`;
}

async function main() {
  console.log('Beautiful Mermaid Diagram Renderer');
  console.log('===================================\n');

  // Ensure output directory exists
  mkdirSync(OUTPUT_DIR, { recursive: true });

  // Find all markdown files
  const mdFiles = findMarkdownFiles(DOCS_DIR);
  console.log(`Found ${mdFiles.length} markdown files\n`);

  const allBlocks = [];
  const mappings = {};

  // Extract all Mermaid blocks
  for (const filePath of mdFiles) {
    const content = readFileSync(filePath, 'utf-8');
    const blocks = extractMermaidBlocks(content, filePath);
    if (blocks.length > 0) {
      console.log(`${filePath.replace(DOCS_DIR + '/', '')}: ${blocks.length} diagram(s)`);
      allBlocks.push(...blocks);
    }
  }

  console.log(`\nTotal: ${allBlocks.length} diagrams to render\n`);

  // Render each diagram
  for (const block of allBlocks) {
    const filename = generateFilename(block.filePath, block.index, block.code);
    const outputPath = join(OUTPUT_DIR, filename);

    try {
      console.log(`  Rendering ${filename}...`);
      const svg = await renderMermaid(block.code, THEME);
      writeFileSync(outputPath, svg);
      console.log(`  Saved ${filename}`);

      // Store mapping
      const relPath = block.filePath.replace(DOCS_DIR + '/', '');
      if (!mappings[relPath]) {
        mappings[relPath] = [];
      }
      mappings[relPath].push({
        original: block.fullMatch,
        imagePath: `/_static/images/diagrams/${filename}`,
        index: block.index,
      });
    } catch (error) {
      console.error(`  Failed to render ${filename}: ${error.message}`);
      console.error(`     Code snippet: ${block.code.slice(0, 100)}...`);
    }
  }

  // Write mappings file for reference
  const mappingsPath = join(OUTPUT_DIR, 'mappings.json');
  writeFileSync(mappingsPath, JSON.stringify(mappings, null, 2));
  console.log(`\nMappings saved to ${mappingsPath}`);

  console.log('\nDone! Now update documentation to reference the SVG images.');
}

main().catch(console.error);
