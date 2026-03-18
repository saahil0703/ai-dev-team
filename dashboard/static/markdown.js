// Simple Markdown Parser for Profit Tracker Dashboard

function parseMarkdown(markdown) {
  if (!markdown || typeof markdown !== 'string') {
    return '<p>No content available</p>';
  }

  let html = markdown;

  // Headers (must be processed before other formatting)
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Code blocks (fenced with ```)
  html = html.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/gim, (match, lang, code) => {
    const className = lang ? `language-${lang}` : '';
    return `<pre class="${className}"><code>${escapeHtml(code.trim())}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');

  // Bold text
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/__(.*?)__/gim, '<strong>$1</strong>');

  // Italic text
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
  html = html.replace(/_(.*?)_/gim, '<em>$1</em>');

  // Strikethrough
  html = html.replace(/~~(.*?)~~/gim, '<del>$1</del>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/gim, '<img src="$2" alt="$1" style="max-width: 100%; height: auto; border-radius: 8px; margin: 1rem 0;" />');

  // Horizontal rules
  html = html.replace(/^---$/gim, '<hr style="border: none; height: 1px; background: var(--glass-border); margin: 2rem 0;" />');
  html = html.replace(/^\*\*\*$/gim, '<hr style="border: none; height: 1px; background: var(--glass-border); margin: 2rem 0;" />');

  // Unordered lists
  html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
  html = html.replace(/^- (.+)$/gim, '<li>$1</li>');
  html = html.replace(/^\+ (.+)$/gim, '<li>$1</li>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>');

  // Wrap consecutive list items in ul/ol tags
  html = html.replace(/(<li>.*<\/li>)/gims, (match) => {
    return `<ul>${match}</ul>`;
  });

  // Blockquotes
  html = html.replace(/^> (.+)$/gim, '<blockquote style="border-left: 3px solid var(--electric-blue); padding-left: 1rem; margin: 1rem 0; font-style: italic; color: var(--text-secondary);">$1</blockquote>');

  // Task lists (GitHub style)
  html = html.replace(/^- \[ \] (.+)$/gim, '<div class="task-item"><input type="checkbox" disabled> $1</div>');
  html = html.replace(/^- \[x\] (.+)$/gim, '<div class="task-item"><input type="checkbox" checked disabled> $1</div>');

  // Tables (basic support)
  html = processMarkdownTables(html);

  // Line breaks and paragraphs
  html = html.replace(/\n\n/gim, '</p><p>');
  html = html.replace(/\n/gim, '<br>');

  // Wrap in paragraphs if not already wrapped in block elements
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }

  // Clean up empty paragraphs and multiple line breaks
  html = html.replace(/<p><\/p>/gim, '');
  html = html.replace(/<br\s*\/?>\s*<br\s*\/?>/gim, '</p><p>');

  return html;
}

function processMarkdownTables(html) {
  // Simple table processing (GitHub flavor markdown)
  const tableRegex = /^(\|.*\|)\n(\|.*\|)\n((\|.*\|(?:\n|$))*)/gm;
  
  return html.replace(tableRegex, (match, header, separator, body) => {
    const headerCells = header.split('|').slice(1, -1).map(cell => cell.trim());
    const bodyRows = body.trim().split('\n').map(row => 
      row.split('|').slice(1, -1).map(cell => cell.trim())
    );

    let tableHtml = '<table style="width: 100%; border-collapse: collapse; margin: 1rem 0; background: var(--glass-bg); border-radius: 8px; overflow: hidden;">';
    
    // Header
    tableHtml += '<thead><tr>';
    headerCells.forEach(cell => {
      tableHtml += `<th style="padding: 0.75rem; background: var(--bg-secondary); color: var(--text-primary); font-weight: 600; border-bottom: 1px solid var(--glass-border);">${cell}</th>`;
    });
    tableHtml += '</tr></thead>';

    // Body
    tableHtml += '<tbody>';
    bodyRows.forEach((row, index) => {
      const bgColor = index % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)';
      tableHtml += `<tr style="background: ${bgColor};">`;
      row.forEach(cell => {
        tableHtml += `<td style="padding: 0.75rem; border-bottom: 1px solid var(--glass-border); color: var(--text-secondary);">${cell}</td>`;
      });
      tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';

    return tableHtml;
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Enhanced code syntax highlighting for common languages
function highlightCode(code, language) {
  if (!language) return escapeHtml(code);

  const keywords = {
    javascript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'class', 'import', 'export', 'async', 'await'],
    python: ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'import', 'from', 'return', 'async', 'await', 'with', 'as'],
    css: ['background', 'color', 'display', 'position', 'margin', 'padding', 'border', 'width', 'height', 'font'],
    html: ['div', 'span', 'p', 'h1', 'h2', 'h3', 'a', 'img', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th']
  };

  let highlighted = escapeHtml(code);

  if (keywords[language]) {
    keywords[language].forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
      highlighted = highlighted.replace(regex, `<span style="color: var(--electric-blue); font-weight: 600;">${keyword}</span>`);
    });
  }

  // Highlight strings
  highlighted = highlighted.replace(/(['"])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span style="color: var(--neon-green);">$1$2$1</span>');
  
  // Highlight comments
  highlighted = highlighted.replace(/(\/\/.*$)/gm, '<span style="color: var(--text-muted); font-style: italic;">$1</span>');
  highlighted = highlighted.replace(/(\/\*[\s\S]*?\*\/)/g, '<span style="color: var(--text-muted); font-style: italic;">$1</span>');
  highlighted = highlighted.replace(/(#.*$)/gm, '<span style="color: var(--text-muted); font-style: italic;">$1</span>');

  return highlighted;
}

// Add custom styles for parsed markdown elements
function addMarkdownStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .task-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0.25rem 0;
      color: var(--text-secondary);
    }
    
    .task-item input[type="checkbox"] {
      accent-color: var(--neon-green);
    }
    
    .task-item input[type="checkbox"]:checked + text {
      text-decoration: line-through;
      color: var(--text-muted);
    }
    
    .meeting-content ul,
    .doc-content ul {
      padding-left: 1.5rem;
      margin: 1rem 0;
    }
    
    .meeting-content ol,
    .doc-content ol {
      padding-left: 1.5rem;
      margin: 1rem 0;
    }
    
    .meeting-content li,
    .doc-content li {
      margin: 0.25rem 0;
      color: var(--text-secondary);
    }
    
    .meeting-content blockquote,
    .doc-content blockquote {
      border-left: 3px solid var(--electric-blue);
      padding-left: 1rem;
      margin: 1rem 0;
      font-style: italic;
      color: var(--text-secondary);
    }
    
    .meeting-content a,
    .doc-content a {
      color: var(--electric-blue);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: border-color 0.3s ease;
    }
    
    .meeting-content a:hover,
    .doc-content a:hover {
      border-bottom-color: var(--electric-blue);
    }
    
    .meeting-content img,
    .doc-content img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      margin: 1rem 0;
      box-shadow: var(--shadow-sm);
    }
    
    .meeting-content hr,
    .doc-content hr {
      border: none;
      height: 1px;
      background: var(--glass-border);
      margin: 2rem 0;
    }
    
    .meeting-content table,
    .doc-content table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
      background: var(--glass-bg);
      border-radius: 8px;
      overflow: hidden;
    }
    
    .meeting-content th,
    .doc-content th {
      padding: 0.75rem;
      background: var(--bg-secondary);
      color: var(--text-primary);
      font-weight: 600;
      border-bottom: 1px solid var(--glass-border);
    }
    
    .meeting-content td,
    .doc-content td {
      padding: 0.75rem;
      border-bottom: 1px solid var(--glass-border);
      color: var(--text-secondary);
    }
    
    .meeting-content tr:nth-child(even),
    .doc-content tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.02);
    }
  `;
  
  document.head.appendChild(style);
}

// Initialize markdown styles when DOM is loaded
document.addEventListener('DOMContentLoaded', addMarkdownStyles);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { parseMarkdown, highlightCode };
}