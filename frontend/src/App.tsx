import { useState } from "react";

type Concept = {
  id: string;
  label: string;
  frequency: number;
};

type Claim = {
  id: string;
  paragraph: number;
  text: string;
  citations: string[];
};

type Section = {
  name: string;
  paragraph_count: number;
  preview: string;
};

type GraphNode = {
  id: string;
  label: string;
  type: string;
  size: number;
};

type GraphEdge = {
  source: string;
  target: string;
  type: string;
};

type Analysis = {
  document: {
    filename: string;
    preview: string;
  };

  stats: {
    words: number;
    paragraphs: number;
    sections: number;
    citations: number;
    claims: number;
    concepts: number;
  };

  sections: Section[];

  citations: string[];

  concepts: Concept[];

  claims: Claim[];

  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
};

const API = "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    if (!file) return;

    setLoading(true);

    const formData = new FormData();

    formData.append("file", file);

    try {
      const response = await fetch(
        `${API}/api/v1/documents/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Document analysis failed.");
      }

      const result = await response.json();

      setAnalysis(result);

    } catch (error) {

      alert(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );

    } finally {

      setLoading(false);

    }
  }

  return (
    <main className="shell">

      {/* HEADER */}

      <header>

        <div className="eyebrow">
          IDEAOS · V0.2
        </div>

        <h1>
          An Operating System for Human Knowledge.
        </h1>

        <p className="subtitle">
          Turn academic documents into structured maps
          of concepts, claims, evidence, and intellectual
          relationships.
        </p>

      </header>


      {/* UPLOAD */}

      <section className="upload-card">

        <label className="dropzone">

          <input
            type="file"
            accept=".pdf"
            onChange={(event) => {

              const selectedFile =
                event.target.files?.[0] ?? null;

              setFile(selectedFile);

              setAnalysis(null);

            }}
          />

          <span>
            {file
              ? file.name
              : "Drop a PDF here or choose a file"}
          </span>

          <small>
            PDF · IdeaOS Document Intelligence
          </small>

        </label>


        <button
          disabled={!file || loading}
          onClick={analyze}
        >

          {loading
            ? "Analyzing..."
            : "Analyze document"}

        </button>

      </section>


      {/* RESULTS */}

      {analysis && (

        <section className="dashboard">


          {/* DOCUMENT */}

          <div className="card">

            <div className="eyebrow">
              DOCUMENT
            </div>

            <h2>
              {analysis.document.filename}
            </h2>

            <p>
              {analysis.stats.words.toLocaleString()} words
              {" · "}
              {analysis.stats.paragraphs} paragraphs
            </p>

          </div>


          {/* CORE STATS */}

          <div className="card">

            <div className="eyebrow">
              KNOWLEDGE STRUCTURE
            </div>

            <div className="stat-grid">

              <div className="stat">
                <strong>
                  {analysis.stats.sections}
                </strong>

                <span>
                  Sections
                </span>
              </div>


              <div className="stat">
                <strong>
                  {analysis.stats.concepts}
                </strong>

                <span>
                  Concepts
                </span>
              </div>


              <div className="stat">
                <strong>
                  {analysis.stats.claims}
                </strong>

                <span>
                  Claims
                </span>
              </div>


              <div className="stat">
                <strong>
                  {analysis.stats.citations}
                </strong>

                <span>
                  Citations
                </span>
              </div>


              <div className="stat">
                <strong>
                  {analysis.graph.nodes.length}
                </strong>

                <span>
                  Graph Nodes
                </span>
              </div>


              <div className="stat">
                <strong>
                  {analysis.graph.edges.length}
                </strong>

                <span>
                  Relationships
                </span>
              </div>

            </div>

          </div>


          {/* CONCEPTS */}

          <div className="card">

            <div className="eyebrow">
              CONCEPTS
            </div>

            <div className="concepts">

              {analysis.concepts.map(
                (concept) => (

                  <span
                    key={concept.id}
                  >

                    {concept.label}

                    {" · "}

                    {concept.frequency}

                  </span>

                )
              )}

            </div>

          </div>


          {/* SECTIONS */}

          <div className="card">

            <div className="eyebrow">
              DOCUMENT STRUCTURE
            </div>

            <div className="sections">

              {analysis.sections.map(
                (section) => (

                  <div
                    className="section-row"
                    key={section.name}
                  >

                    <span>
                      {section.name.replace(/_/g, " ")}
                    </span>

                    <small>
                      {section.paragraph_count}
                      {" paragraphs"}
                    </small>

                  </div>

                )
              )}

            </div>

          </div>


          {/* CLAIMS */}

          <div className="card full">

            <div className="eyebrow">
              CLAIMS & ARGUMENTS
            </div>

            {analysis.claims.length === 0 ? (

              <p>
                No argument-like claims detected
                by the current rule-based extractor.
              </p>

            ) : (

              analysis.claims
                .slice(0, 10)
                .map((claim) => (

                  <div
                    className="claim"
                    key={claim.id}
                  >

                    <span>
                      {claim.text}
                    </span>

                    <small>

                      Paragraph {claim.paragraph}

                      {" · "}

                      {claim.citations.length}
                      {" citation(s)"}

                    </small>

                  </div>

                ))

            )}

          </div>


          {/* IDEA GRAPH */}

          <div className="card full">

            <div className="eyebrow">
              IDEA GRAPH · MVP
            </div>

            <p>
              {analysis.graph.nodes.length}
              {" nodes · "}
              {analysis.graph.edges.length}
              {" relationships"}
            </p>

            <div className="graph">

              {analysis.graph.nodes
                .filter(
                  (node) =>
                    node.type === "concept"
                )
                .slice(0, 16)
                .map((node, index) => (

                  <div
                    className="node"
                    key={node.id}
                    title={`${node.label} · ${node.size}`}
                    style={{
                      left:
                        `${20 + (index % 4) * 24}%`,

                      top:
                        `${25 + Math.floor(index / 4) * 23}%`
                    }}
                  >

                    {node.label}

                  </div>

                ))}

            </div>

          </div>


          {/* CITATIONS */}

          <div className="card">

            <div className="eyebrow">
              CITATIONS DETECTED
            </div>

            <div className="concepts">

              {analysis.citations
                .slice(0, 30)
                .map(
                  (citation, index) => (

                    <span key={index}>
                      {citation}
                    </span>

                  )
                )}

            </div>

          </div>


          {/* TEXT PREVIEW */}

          <div className="card">

            <div className="eyebrow">
              SOURCE TEXT
            </div>

            <pre>
              {analysis.document.preview}
            </pre>

          </div>

        </section>

      )}

    </main>
  );
}
