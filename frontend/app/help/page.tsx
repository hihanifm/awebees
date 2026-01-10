"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, HelpCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";
import { useTranslation } from "@/lib/i18n";
import { StatusBar } from "@/components/StatusBar";
import { logger } from "@/lib/logger";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Initialize Mermaid once
let mermaidInitialized = false;

// Mermaid Diagram Component
function MermaidDiagram({ diagram }: { diagram: string }) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const diagramIdRef = useRef<string>(`mermaid-${Math.random().toString(36).substring(7)}`);

  useEffect(() => {
    if (!diagram) return;

    // Initialize mermaid once globally
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
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
        },
      });
      mermaidInitialized = true;
    }

    const renderMermaid = async () => {
      try {
        // Clear previous content
        setSvg("");
        setError(null);
        
        // Render the diagram
        const { svg: renderedSvg } = await mermaid.render(diagramIdRef.current, diagram.trim());
        setSvg(renderedSvg);
      } catch (err) {
        logger.error("Error rendering Mermaid diagram:", err);
        setError(err instanceof Error ? err.message : "Failed to render diagram");
        setSvg("");
      }
    };

    renderMermaid();
  }, [diagram]);

  if (error) {
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-4 my-4 dark:border-red-800 dark:bg-red-950">
        <p className="text-sm text-red-600 dark:text-red-400">
          Failed to render diagram: {error}
        </p>
        <pre className="mt-2 text-xs bg-red-100 dark:bg-red-900 p-2 rounded overflow-x-auto">
          {diagram}
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="rounded-md border border-border bg-muted p-4 my-4 flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Rendering diagram...</p>
      </div>
    );
  }

  return (
    <div className="my-6 flex justify-center overflow-x-auto bg-background rounded-lg border border-border p-4">
      {svg ? (
        <div 
          className="mermaid-container"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      ) : !error ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
          <span className="text-sm">Rendering diagram...</span>
        </div>
      ) : null}
      {error && (
        <div className="w-full">
          <div className="rounded-md border border-red-300 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <p className="text-sm text-red-600 dark:text-red-400 mb-2">
              Failed to render diagram: {error}
            </p>
            <pre className="text-xs bg-red-100 dark:bg-red-900 p-2 rounded overflow-x-auto text-red-800 dark:text-red-200">
              {diagram}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function HelpPage() {
  const { t } = useTranslation();
  const [markdownContent, setMarkdownContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHelpContent = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const baseUrl = API_URL || "";
        const url = baseUrl ? `${baseUrl}/api/help` : "/api/help";
        
        logger.info(`Fetching help content from: ${url}`);
        
        const response = await fetch(url);
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => "Unknown error");
          throw new Error(`Failed to load help content: ${response.status} ${errorText}`);
        }
        
        const content = await response.text();
        setMarkdownContent(content);
        logger.info(`Successfully loaded help content (${content.length} characters)`);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load help content";
        logger.error("Error fetching help content:", err);
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchHelpContent();
  }, []);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 font-sans">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-6 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary/10 via-accent/5 to-primary/10 -mx-4 px-6 py-4">
          <Link 
            href="/"
            className="inline-flex items-center text-sm text-primary hover:text-primary/80 mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            {t("app.backToAnalysis")}
          </Link>
          <div className="flex items-center gap-3">
            <HelpCircle className="h-8 w-8 text-primary" />
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
              {t("app.help") || "Help"}
            </h1>
          </div>
          <p className="text-foreground/80 mt-2 font-medium">
            {t("app.helpDescription") || "Quick Start Guide"}
          </p>
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
              <ReactMarkdown
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
                    // Don't render paragraph if it contains a code block (handled by pre)
                    if (node.children?.some((child: any) => child.type === 'element' && child.tagName === 'pre')) {
                      return <>{children}</>;
                    }
                    return (
                      <p className="text-foreground leading-7 mb-4" {...props}>
                        {children}
                      </p>
                    );
                  },
                  // Inline code
                  code({ node, inline, className, children, ...props }) {
                    if (inline) {
                      return (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground border border-border" {...props}>
                          {children}
                        </code>
                      );
                    }
                    // For block code, just return code element (pre handles the wrapper and mermaid detection)
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                  // Code blocks wrapper - handle mermaid here
                  pre({ node, children, ...props }) {
                    // Check if this is a mermaid diagram by examining the node
                    if (node.children && node.children.length > 0) {
                      const codeChild = node.children[0] as any;
                      if (codeChild && codeChild.type === 'element' && codeChild.tagName === 'code') {
                        const className = codeChild.properties?.className;
                        const classNameStr = Array.isArray(className) 
                          ? className.join(' ') 
                          : (typeof className === 'string' ? className : '');
                        
                        if (classNameStr.includes('language-mermaid')) {
                          // Extract diagram content from code child's text nodes
                          const extractText = (nodes: any[]): string => {
                            return nodes
                              .filter((n: any) => n.type === 'text')
                              .map((n: any) => n.value || '')
                              .join('');
                          };
                          const diagram = extractText(codeChild.children || []);
                          if (diagram.trim()) {
                            return <MermaidDiagram diagram={diagram.trim()} />;
                          }
                        }
                      }
                    }
                    
                    // Regular code block
                    return (
                      <pre className="rounded-lg border border-border bg-muted p-4 overflow-x-auto my-4 text-sm font-mono" {...props}>
                        {children}
                      </pre>
                    );
                  },
                  // Links
                  a({ node, href, children, ...props }) {
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
                  // Images
                  img({ node, src, alt, ...props }) {
                    return (
                      <img 
                        src={src} 
                        alt={alt} 
                        className="max-w-full h-auto rounded-lg border border-border my-6 shadow-sm" 
                        {...props} 
                      />
                    );
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
