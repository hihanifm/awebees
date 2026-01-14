"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { HelpCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";
import { useTranslation } from "@/lib/i18n";
import { StatusBar } from "@/components/StatusBar";
import { logger } from "@/lib/logger";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Initialize Mermaid once
let mermaidInitialized = false;

// Image Component with Error Handling
// Note: This component is used within ReactMarkdown's img component.
// ReactMarkdown wraps images in <p> tags, but our p component checks for img elements
// and doesn't wrap them, so block-level elements (like div) are safe to return.
function MarkdownImage({ src, alt, ...props }: { src?: string; alt?: string; [key: string]: any }) {
  const [imageError, setImageError] = useState(false);
  
  if (!src) return null;
  
  if (imageError) {
    // Return a block-level element - the p component will detect img and not wrap it
    return (
      <div className="rounded-lg border border-border bg-muted p-4 flex items-center gap-2 text-muted-foreground my-4">
        <span className="text-sm">⚠️ Image not found: {alt || src}</span>
      </div>
    );
  }
  
  return (
    <img 
      src={src} 
      alt={alt || ''} 
      className="max-w-full h-auto rounded-lg border border-border shadow-sm my-4 block" 
      onError={() => setImageError(true)}
      {...props} 
    />
  );
}

// Mermaid Diagram Component - using auto-rendering approach
function MermaidDiagram({ diagram }: { diagram: string }) {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(true);

  useEffect(() => {
    if (!diagram || !diagramRef.current) {
      logger.warn(`⚠️ MermaidDiagram: missing diagram or ref`);
      return;
    }

    logger.info(`🎨 MermaidDiagram rendering: diagram length=${diagram.length} chars`);
    logger.debug(`   Diagram content: ${diagram.substring(0, 300)}...`);

    // Check if mermaid is available
    if (!mermaid || typeof mermaid.initialize !== 'function') {
      const errorMsg = "Mermaid library not available";
      logger.error(`❌ ${errorMsg}`);
      setError(errorMsg);
      setIsRendering(false);
      return;
    }

    // Initialize mermaid once globally
    if (!mermaidInitialized) {
      try {
        logger.info(`🔧 Initializing Mermaid...`);
        mermaid.initialize({
          startOnLoad: true,
          theme: 'default',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis',
          },
          themeVariables: {
            primaryColor: '#f59e0b',
            primaryTextColor: '#fff',
            primaryBorderColor: '#d97706',
            lineColor: '#94a3b8',
            secondaryColor: '#fbbf24',
            tertiaryColor: '#f3f4f6',
            background: '#ffffff',
            mainBkg: '#ffffff',
            secondBkg: '#f3f4f6',
            textColor: '#1f2937',
            fontSize: '16px',
            fontFamily: 'inherit',
          },
        });
        mermaidInitialized = true;
        logger.info(`✅ Mermaid initialized successfully`);
      } catch (err) {
        const errorMsg = `Failed to initialize Mermaid: ${err instanceof Error ? err.message : String(err)}`;
        logger.error(`❌ ${errorMsg}`, err);
        setError(errorMsg);
        setIsRendering(false);
        return;
      }
    }

    const renderMermaid = async () => {
      try {
        setIsRendering(true);
        setError(null);
        const diagramText = diagram.trim();
        
        if (!diagramText || diagramText.length < 10) {
          throw new Error(`Diagram text is empty or too short: "${diagramText}"`);
        }
        
        logger.info(`🔄 Rendering Mermaid diagram`);
        logger.debug(`   Diagram text: ${diagramText.substring(0, 200)}...`);
        
        if (!diagramRef.current) {
          throw new Error("Diagram ref is null");
        }
        
        // Generate unique ID for this diagram
        const diagramId = `mermaid-${Date.now()}-${Math.random().toString(36).substring(7)}`;
        
        // Set the diagram text content in the div - Mermaid will look for elements with class "mermaid"
        diagramRef.current.textContent = diagramText;
        diagramRef.current.className = 'mermaid';
        diagramRef.current.id = diagramId;
        
        logger.info(`   Set diagram content in div with ID: ${diagramId}`);
        
        // Use mermaid.render() to render the diagram programmatically
        // This is the correct API for mermaid v11+
        const { svg } = await mermaid.render(diagramId, diagramText);
        
        logger.info(`✅ Mermaid rendered successfully: SVG length=${svg.length} chars`);
        
        // Process SVG to make it responsive
        let processedSvg = svg;
        processedSvg = processedSvg.replace(/width="[^"]*"/g, '');
        processedSvg = processedSvg.replace(/height="[^"]*"/g, '');
        
        if (processedSvg.includes('style=')) {
          processedSvg = processedSvg.replace(
            /style="([^"]*)"/,
            'style="$1 width: 100%; max-width: 100%; height: auto; min-width: 800px;"'
          );
        } else {
          processedSvg = processedSvg.replace(
            /<svg/,
            '<svg style="width: 100%; max-width: 100%; height: auto; min-width: 800px;"'
          );
        }
        
        // Set the rendered SVG as innerHTML
        if (diagramRef.current) {
          diagramRef.current.innerHTML = processedSvg;
          logger.info(`✅ SVG set in div element`);
        }
        
        setIsRendering(false);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Failed to render diagram";
        logger.error(`❌ Error rendering Mermaid diagram:`, err);
        logger.error(`   Error details:`, {
          message: errorMsg,
          diagram: diagram.substring(0, 200),
          stack: err instanceof Error ? err.stack : undefined
        });
        setError(errorMsg);
        setIsRendering(false);
      }
    };

    renderMermaid();
  }, [diagram]);

  if (error) {
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-4 my-6 dark:border-red-800 dark:bg-red-950">
        <p className="text-sm text-red-600 dark:text-red-400 mb-2">
          Failed to render diagram: {error}
        </p>
        <pre className="text-xs bg-red-100 dark:bg-red-900 p-2 rounded overflow-x-auto text-red-800 dark:text-red-200">
          {diagram}
        </pre>
      </div>
    );
  }

  return (
    <div className="my-8 w-full">
      <div 
        className="mermaid-container w-full flex justify-center overflow-x-auto bg-background rounded-lg border border-border p-6"
        style={{ minHeight: '400px' }}
      >
        {isRendering && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
              <span className="text-sm">Rendering diagram...</span>
            </div>
          </div>
        )}
        <div 
          ref={diagramRef}
          className="mermaid w-full max-w-5xl flex justify-center"
          style={{ 
            minHeight: '400px',
          }}
        />
      </div>
    </div>
  );
}

export default function HelpPage() {
  const { t } = useTranslation();
  const [markdownContent, setMarkdownContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentStack, setDocumentStack] = useState<Array<{ path: string; title: string }>>([
    { path: "", title: "Quick Start Guide" }
  ]);
  const [mermaidDiagrams, setMermaidDiagrams] = useState<Array<{ id: string; content: string }>>([]);
  const fetchingRef = useRef(false);
  const lastFetchedPathRef = useRef<string | null>(null);
  
  const fetchMarkdownContent = useCallback(async (docPath: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const baseUrl = API_URL || "";
      let url: string;
      
      if (!docPath || docPath === "") {
        // Fetch Quick Start guide
        url = baseUrl ? `${baseUrl}/api/help` : "/api/help";
        logger.info(`📖 Fetching Quick Start guide (empty path)`);
      } else {
        // Fetch specific documentation file
        // Normalize path - remove leading slash if present, normalize Windows paths
        let normalizedPath = docPath
          .startsWith('/') ? docPath.slice(1) : docPath;
        normalizedPath = normalizedPath.replace(/\\/g, '/'); // Normalize Windows paths
        
        url = baseUrl ? `${baseUrl}/api/help/docs/${normalizedPath}` : `/api/help/docs/${normalizedPath}`;
        logger.info(`📖 Fetching document: "${docPath}" -> normalized: "${normalizedPath}"`);
      }
      
      logger.info(`🌐 Full API URL: ${url}`);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => "Unknown error");
        throw new Error(`Failed to load help content: ${response.status} ${errorText}`);
      }
      
      let content = await response.text();
      logger.info(`📄 Received content (${content.length} chars) for path: "${docPath || '(home)'}"`);
      logger.info(`📝 Content preview (first 200 chars): ${content.substring(0, 200).replace(/\n/g, '\\n')}`);
      
      // Extract Mermaid diagrams from raw markdown before ReactMarkdown parses it
      const mermaidBlocks: Array<{ id: string; content: string }> = [];
      
      const transformContent = (text: string) => {
        // Extract all Mermaid diagrams and store them
        text = text.replace(
          /```mermaid\s*\n([\s\S]*?)```/gi,
          (match, diagramContent) => {
            const diagramText = diagramContent.trim();
            const diagramId = `mermaid-${mermaidBlocks.length}`;
            mermaidBlocks.push({ id: diagramId, content: diagramText });
            logger.info(`📊 Extracted Mermaid diagram "${diagramId}": ${diagramText.length} chars`);
            logger.debug(`   Diagram preview: ${diagramText.substring(0, 200)}...`);
            // Remove mermaid block from markdown (replace with empty line to preserve spacing)
            return '\n\n';
          }
        );
        
        // Store extracted diagrams in state (set immediately after transformation)
        if (mermaidBlocks.length > 0) {
          setMermaidDiagrams(mermaidBlocks);
          logger.info(`📊 Stored ${mermaidBlocks.length} Mermaid diagram(s) to render separately`);
        } else {
          setMermaidDiagrams([]);
        }
        
        return text;
        
        // Transform relative image paths to use the backend API endpoint
        text = text.replace(
          /!\[([^\]]*)\]\(([^)]+\.(png|jpg|jpeg|gif|svg|webp))\)/gi,
          (match, alt, imagePath) => {
            // If it's already an absolute URL (http/https), leave it as is
            if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
              return match;
            }
            // If it's already an absolute path starting with /api/help/images, leave it as is
            if (imagePath.startsWith('/api/help/images')) {
              return match;
            }
            // Otherwise, convert relative path to API endpoint
            const imageName = imagePath.split('/').pop()?.split('\\').pop() || imagePath;
            const imageApiPath = baseUrl 
              ? `${baseUrl}/api/help/images/${imageName}`
              : `/api/help/images/${imageName}`;
            return `![${alt}](${imageApiPath})`;
          }
        );
        
        // Normalize internal markdown file links (keep .md extension for detection)
        // Match markdown links: [text](file.md) or [text](path/to/file.md)
        text = text.replace(
          /\[([^\]]+)\]\(([^)]+\.md)\)/gi,
          (match, linkText, filePath) => {
            // Skip external URLs
            if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
              return match;
            }
            // Skip if already an absolute API path
            if (filePath.startsWith('/api/help/docs/')) {
              logger.debug(`Link already has API path, skipping: "${filePath}"`);
              return match;
            }
            // Normalize path - remove leading ./ or ../ if present, normalize separators
            // Keep it as a relative path so ReactMarkdown parses it correctly
            let normalizedPath = filePath
              .replace(/^\.\//g, '')
              .replace(/^\.\.\//g, '')
              .replace(/\\/g, '/') // Normalize Windows paths
              .trim();
            
            logger.info(`🔄 Normalizing markdown link: "${filePath}" -> "${normalizedPath}" (link text: "${linkText}")`);
            // Return with normalized path - ReactMarkdown will parse it as href
            return `[${linkText}](${normalizedPath})`;
          }
        );
        
        return text;
      };
      
      content = transformContent(content);
      setMarkdownContent(content);
      logger.info(`✅ Successfully loaded and transformed content (${content.length} chars) for path: "${docPath || '(home)'}"`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load help content";
      logger.error("Error fetching help content:", err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch content when document stack changes
  useEffect(() => {
    if (documentStack.length === 0) {
      return;
    }
    
    const currentDoc = documentStack[documentStack.length - 1];
    const pathToFetch = currentDoc?.path || "";
    const pathKey = pathToFetch || "__HOME__";
    
    // Only fetch if this is a different path than what we last fetched
    const lastFetched = lastFetchedPathRef.current;
    logger.info(`🔄 Document stack changed - Stack length: ${documentStack.length}`);
    logger.info(`📄 Current document: path="${pathToFetch || '(home - Quick Start)'}", title="${currentDoc?.title || ''}"`);
    logger.info(`📚 Full stack: ${documentStack.map((d, i) => `${i}: "${d.path || '(home)'}" (${d.title})`).join(' → ')}`);
    logger.info(`🔍 Path check: lastFetched="${lastFetched}", currentPathKey="${pathKey}"`);
    
    if (lastFetched === pathKey) {
      logger.debug(`⏸️ Path unchanged: "${pathToFetch || '(home)'}", skipping fetch (already loaded)`);
      return;
    }
    
    // If already fetching, log it but continue with new fetch
    if (fetchingRef.current) {
      logger.warn(`⚠️ Fetch already in progress for "${lastFetched}", but path changed to "${pathKey}" - starting new fetch`);
    }
    
    logger.info(`📥 Starting fetch for document: "${pathToFetch || '(home - Quick Start)'}" (key: "${pathKey}")`);
    logger.info(`🔗 API URL will be: ${pathToFetch ? `/api/help/docs/${pathToFetch}` : '/api/help'}`);
    
    // Set fetching flag to prevent duplicate requests
    fetchingRef.current = true;
    
    // Clear previous content while loading new one
    setMarkdownContent("");
    
    fetchMarkdownContent(pathToFetch)
      .then(() => {
        logger.info(`✅ Successfully loaded document: "${pathToFetch || '(home - Quick Start)'}"`);
        // Only update ref AFTER successful fetch
        lastFetchedPathRef.current = pathKey;
      })
      .catch((err) => {
        logger.error(`❌ Failed to load document: "${pathToFetch || '(home - Quick Start)'}"`, err);
        // Reset ref on error so we can retry
        lastFetchedPathRef.current = null;
      })
      .finally(() => {
        fetchingRef.current = false;
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentStack]);

  // Update document title from markdown content when it loads
  useEffect(() => {
    if (!markdownContent || documentStack.length === 0) return;
    
    const h1Match = markdownContent.match(/^#\s+(.+)$/m);
    if (!h1Match) return;
    
    setDocumentStack(prev => {
      if (prev.length === 0) return prev;
      
      const currentDocIndex = prev.length - 1;
      const currentDoc = prev[currentDocIndex];
      if (!currentDoc) return prev;
      
      const extractedTitle = h1Match[1].trim();
      if (!extractedTitle || extractedTitle === currentDoc.title) {
        return prev; // No change needed - return same reference to prevent re-fetch
      }
      
      // Only update if title is a default/generic title (not yet extracted from content)
      const filenameTitle = currentDoc.path.split('/').pop()?.replace('.md', '') || '';
      const isDefaultTitle = 
        currentDoc.title === filenameTitle || 
        currentDoc.title === 'Documentation' || 
        (!currentDoc.path && currentDoc.title === 'Quick Start Guide');
      
      if (isDefaultTitle) {
        logger.info(`📝 Extracting title from H1: "${currentDoc.title}" -> "${extractedTitle}" (path: "${currentDoc.path || '(home)'}")`);
        // Create new array with updated title - same path, so fetch will be skipped
        const newStack = [...prev];
        newStack[currentDocIndex] = { ...newStack[currentDocIndex], title: extractedTitle };
        // The path is the same, so the fetch useEffect will see lastFetchedPathRef.current === pathToFetch and skip
        return newStack;
      }
      
      return prev; // Title already set from content, return same reference
    });
  }, [markdownContent]);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 font-sans">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-6 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary/10 via-accent/5 to-primary/10 -mx-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <HelpCircle className="h-8 w-8 text-primary" />
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
              {t("app.help") || "Help"}
            </h1>
          </div>
          <p className="text-foreground/80 mt-2 font-medium">
            {t("app.helpDescription") || "Quick Start Guide"}
          </p>
          
          {/* Breadcrumb Navigation */}
          {documentStack.length > 1 && (
            <div className="flex items-center gap-2 mt-4 text-sm text-muted-foreground flex-wrap">
              {documentStack.map((doc, index) => (
                <div key={`${doc.path}-${index}`} className="flex items-center gap-2">
                  {index > 0 && <span>/</span>}
                  {index === documentStack.length - 1 ? (
                    <span className="text-foreground font-medium">{doc.title}</span>
                  ) : (
                    <button
                      onClick={() => {
                        const newStack = documentStack.slice(0, index + 1);
                        setDocumentStack(newStack);
                      }}
                      className="text-primary hover:underline cursor-pointer"
                    >
                      {doc.title}
                    </button>
                  )}
                </div>
              ))}
              {documentStack.length > 1 && (
                <button
                  onClick={() => {
                    setDocumentStack([{ path: "", title: "Quick Start Guide" }]);
                  }}
                  className="ml-2 px-2 py-1 text-xs rounded border border-border hover:bg-muted text-primary hover:bg-muted/80 transition-colors"
                >
                  ← Back to Home
                </button>
              )}
            </div>
          )}
        </div>

        {/* Content */}
        <section className="space-y-4">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">{t("common.loading") || "Loading..."}</p>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
              <p className="text-sm text-red-600 dark:text-red-400">
                {t("common.error") || "Error"}: {error}
              </p>
            </div>
          )}

              {!loading && !error && markdownContent && (
            <div className="max-w-none space-y-6">
              {/* Debug: Show current document path */}
              {documentStack.length > 0 && (
                <div className="text-xs text-muted-foreground mb-2 p-2 bg-muted rounded border border-border">
                  📄 <strong>Current document:</strong> <code className="px-2 py-1 bg-background rounded font-mono text-primary">{documentStack[documentStack.length - 1].path || '(home - QUICK_START.md)'}</code>
                  <span className="ml-2 text-muted-foreground">
                    | Content length: {markdownContent.length} chars
                    {mermaidDiagrams.length > 0 && ` | Mermaid diagrams: ${mermaidDiagrams.length}`}
                  </span>
                </div>
              )}
              
              {/* Render Mermaid diagrams separately (extracted before ReactMarkdown parsing) */}
              {mermaidDiagrams.length > 0 && (
                <div className="space-y-6">
                  {mermaidDiagrams.map((diagram, index) => (
                    <div key={diagram.id}>
                      <MermaidDiagram diagram={diagram.content} />
                    </div>
                  ))}
                </div>
              )}
              
              <ReactMarkdown
                key={documentStack.length > 0 ? documentStack[documentStack.length - 1].path || 'home' : 'home'}
                components={{
                  // Headings with better styling
                  h1({ node, children, ...props }) {
                    return (
                      <h1 className="text-3xl font-bold text-foreground mt-8 mb-4 pb-2 border-b border-border" {...props}>
                        {children}
                      </h1>
                    );
                  },
                  h2({ node, children, ...props }) {
                    return (
                      <h2 className="text-2xl font-semibold text-foreground mt-6 mb-3" {...props}>
                        {children}
                      </h2>
                    );
                  },
                  h3({ node, children, ...props }) {
                    return (
                      <h3 className="text-xl font-semibold text-foreground mt-4 mb-2" {...props}>
                        {children}
                      </h3>
                    );
                  },
                  // Paragraphs with better spacing
                  p({ node, children, ...props }) {
                    // Don't wrap if paragraph contains block-level elements (pre, img)
                    // ReactMarkdown wraps images in <p> by default, but we want block-level rendering
                    if (node?.children && Array.isArray(node.children)) {
                      const hasBlockElement = node.children.some((child: any) => 
                        child && child.type === 'element' && 
                        (child.tagName === 'pre' || child.tagName === 'img')
                      );
                      
                      if (hasBlockElement) {
                        // Return children without p wrapper for block elements
                        return <>{children}</>;
                      }
                    }
                    
                    return (
                      <p className="text-foreground leading-7 mb-4" {...props}>
                        {children}
                      </p>
                    );
                  },
                  // Inline code
                  code({ node, className, children, ...props }: any) {
                    const classNameStr = Array.isArray(className) 
                      ? className.join(' ') 
                      : (typeof className === 'string' ? className : '');
                    
                    const isInline = !classNameStr || !classNameStr.includes('language-');
                    
                    if (isInline) {
                      return (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground border border-border" {...props}>
                          {children}
                        </code>
                      );
                    }
                    
                    // For block code, just return code element (pre handles wrapper)
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                  // Code blocks wrapper (mermaid already extracted)
                  pre({ node, children, ...props }: any) {
                    return (
                      <pre className="rounded-lg border border-border bg-muted p-4 overflow-x-auto my-4 text-sm font-mono" {...props}>
                        {children}
                      </pre>
                    );
                  },
                  // Links
                  a({ node, href, children, ...props }) {
                    // Log all links for debugging
                    logger.debug(`🔗 Rendering link: href="${href}", children="${String(children).substring(0, 50)}"`);
                    
                    // Handle internal document links - check if href ends with .md
                    // This catches links like [text](README.md), [text](docs/file.md), etc.
                    if (href && typeof href === 'string' && href.endsWith('.md') && !href.startsWith('http://') && !href.startsWith('https://')) {
                      const docPath = href.trim();
                      // Extract title from link text, or derive from filename
                      const linkText = String(children).trim();
                      const docTitle = linkText || docPath.split('/').pop()?.replace('.md', '') || 'Documentation';
                      
                      logger.info(`🔗 Rendering internal markdown link:`);
                      logger.info(`   href="${href}"`);
                      logger.info(`   docPath="${docPath}"`);
                      logger.info(`   linkText="${linkText}"`);
                      logger.info(`   docTitle="${docTitle}"`);
                      
                      // Ensure docPath is not empty
                      if (!docPath || docPath === '') {
                        logger.error(`❌ ERROR: Internal link has empty path! href="${href}"`);
                        return (
                          <a href="#" className="text-red-500" {...props}>
                            {children} [ERROR: Empty path]
                          </a>
                        );
                      }
                      
                      return (
                        <a
                          href="#"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation(); // Prevent event bubbling
                            
                            const clickedPath = docPath; // Capture in closure
                            const clickedTitle = docTitle;
                            
                            logger.info(`🔗 Internal markdown link clicked:`);
                            logger.info(`   Original href: "${href}"`);
                            logger.info(`   Extracted path: "${clickedPath}"`);
                            logger.info(`   Link text: "${linkText}"`);
                            logger.info(`   Document title: "${clickedTitle}"`);
                            
                            if (!clickedPath || clickedPath === '') {
                              logger.error(`❌ ERROR: Cannot navigate to empty path!`);
                              return;
                            }
                            
                            setDocumentStack(prev => {
                              // Check if this document is already in the stack to avoid duplicates
                              const existingIndex = prev.findIndex(doc => doc.path === clickedPath);
                              if (existingIndex >= 0) {
                                // Navigate to existing document in stack
                                logger.info(`📍 Document already in stack at index ${existingIndex}, navigating back to it`);
                                const newStack = prev.slice(0, existingIndex + 1);
                                logger.info(`📍 New stack: ${newStack.map((d, i) => `${i}: "${d.path || '(home)'}"`).join(' → ')}`);
                                return newStack;
                              } else {
                                // Add new document to stack
                                logger.info(`➕ Adding new document to stack: path="${clickedPath}", title="${clickedTitle}"`);
                                logger.info(`   Previous stack length: ${prev.length}`);
                                logger.info(`   Previous last path: "${prev[prev.length - 1]?.path || '(none)'}"`);
                                const newStack = [...prev, { path: clickedPath, title: clickedTitle }];
                                logger.info(`   New stack length: ${newStack.length}`);
                                logger.info(`   New stack paths: ${newStack.map((d, i) => `${i}: "${d.path || '(home)'}"`).join(' → ')}`);
                                logger.info(`   Last document in new stack: path="${newStack[newStack.length - 1].path}", title="${newStack[newStack.length - 1].title}"`);
                                return newStack;
                              }
                            });
                          }}
                          className="text-primary hover:underline font-medium cursor-pointer"
                          {...props}
                        >
                          {children}
                        </a>
                      );
                    }
                    
                    // External links
                    return (
                      <a
                        href={href}
                        target={href?.startsWith('http') ? '_blank' : undefined}
                        rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
                        className="text-primary hover:underline font-medium"
                        {...props}
                      >
                        {children}
                      </a>
                    );
                  },
                  // Images - render as block-level element
                  img({ node, src, alt, ...props }) {
                    // In markdown, src is always a string (URL), but TypeScript types are broad
                    const srcString = typeof src === 'string' ? src : undefined;
                    // The p component checks for img elements and won't wrap them
                    // MarkdownImage handles its own error state and returns appropriate elements
                    return <MarkdownImage src={srcString} alt={alt} {...props} />;
                  },
                  // Lists
                  ul({ node, children, ...props }) {
                    return (
                      <ul className="list-disc list-outside ml-6 mb-4 text-foreground space-y-2" {...props}>
                        {children}
                      </ul>
                    );
                  },
                  ol({ node, children, ...props }) {
                    return (
                      <ol className="list-decimal list-outside ml-6 mb-4 text-foreground space-y-2" {...props}>
                        {children}
                      </ol>
                    );
                  },
                  li({ node, children, ...props }) {
                    return (
                      <li className="text-foreground leading-7" {...props}>
                        {children}
                      </li>
                    );
                  },
                  // Blockquotes
                  blockquote({ node, children, ...props }) {
                    return (
                      <blockquote className="border-l-4 border-primary pl-4 py-2 my-4 italic text-muted-foreground bg-muted/50 rounded-r" {...props}>
                        {children}
                      </blockquote>
                    );
                  },
                  // Horizontal rules
                  hr({ node, ...props }) {
                    return <hr className="my-8 border-border" {...props} />;
                  },
                  // Strong/bold
                  strong({ node, children, ...props }) {
                    return (
                      <strong className="font-semibold text-foreground" {...props}>
                        {children}
                      </strong>
                    );
                  },
                  // Emphasis/italic
                  em({ node, children, ...props }) {
                    return (
                      <em className="italic text-foreground" {...props}>
                        {children}
                      </em>
                    );
                  },
                }}
              >
                {markdownContent}
              </ReactMarkdown>
            </div>
          )}
        </section>
      </main>

      <StatusBar />
    </div>
  );
}
