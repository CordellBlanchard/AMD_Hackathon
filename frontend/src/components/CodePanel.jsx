import { Badge, Form } from "react-bootstrap";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useEffect, useMemo, useState, useRef } from "react";
import { solarizedDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { Button, CloseButton, Spinner } from "react-bootstrap";
import axios from "axios";

const CodePanel = (props) => {
  const [language, setLanguage] = useState("cpp");
  const [expand, setExpand] = useState(-1);
  const [codeString, setCodeString] = useState("");
  const [highlights, setHighlights] = useState([]);
  const [loading, setLoading] = useState(false);

  const sectionRef = useRef(null);
  const scrollToSection = () => {
    sectionRef.current.scrollIntoView({ behavior: "smooth" });
  };

  const fetchCode = async (blame) => {
    // TODO: move these to env or fetch from backend
    console.log(blame);
    const OWNER = "tensorflow";
    const REPO = "tensorflow";
    const url = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${blame.blame.file}`;
    const headers = {
      Accept: "application/vnd.github.v3.raw",
      // "Authorization": `token ${TOKEN}` // If authentication is required
    };
    const params = {
      ref: blame.issue.commit,
    };

    try {
      const response = await axios.get(url, {
        headers,
        params,
      });

      if (response.status === 200) {
        const content = response.data;
        return content;
      } else {
        console.log(`Error: ${response.status}`);
        throw new Error(`Error: ${response.status}`);
      }
    } catch (error) {
      console.log(`Error: ${error}`);
      throw error;
    }
  };

  useEffect(() => {
    if (props.blame !== null) setLoading(true);
    fetchCode(props.blame).then((code) => {
      setCodeString(code);
      setLoading(false);
    }).catch((error)=>{setLoading(false)});
    // TODO: lines[0] is temporary, need to assign line number to corresponding files once multi-line display is implemented
    setHighlights([
      [props.blame.issue.lines[0], props.blame.issue.lines[0]],
    ]);
  }, [props.blame]);

  // for each highlight, divide the codeString by lines before, the line itself, and after the highlighted line in an array
  // do this to split up the code into a list of lines, and for each line in the list, add an extra attribute to indicate whether it's highlighted
  // then return the array

  const codeLineBlocks = useMemo(() => {
    const lines = codeString.split("\n");
    const splitLines = [];

    let start = 0;
    for (const highlight of highlights) {
      const end = highlight[0] - 1;
      splitLines.push({
        text: lines.slice(start, end).join("\n"),
        highlight: false,
        start: start,
      });
      splitLines.push({
        text: lines.slice(end, highlight[1]).join("\n"),
        highlight: true,
        start: end,
      });
      start = highlight[1];
    }

    splitLines.push({
      text: lines.slice(start).join("\n"),
      highlight: false,
      start: start,
    });

    console.log(splitLines);

    return splitLines;
  }, [codeString, highlights]);

  const highlightedBlocks = useMemo(
    () =>
      codeLineBlocks.map((block, i) => (
        <div>
          {block.highlight ? <div ref={sectionRef}></div> : ""}
          <SyntaxHighlighter
            onClick={() => {
              if (block.highlight) {
                setExpand(expand >= 0 ? -1 : i);
              }
            }}
            className={
              "w-100 m-0 p-0 " + (block.highlight ? "codeblock-highlight" : "")
            }
            language={language}
            style={vscDarkPlus}
            showLineNumbers
            startingLineNumber={block.start + 1}
          >
            {block.text}
          </SyntaxHighlighter>
          <>
            {i === expand ? (
              <div className="text-start m-2 border rounded p-2 bg-secondary bg-opacity-25">
                <Badge className="float-end">Resolved</Badge>
                <div className="">Issue: <span className="text-warning">{props.blame.issue.rule[0].name} </span></div>
                <div className="">Description: <span className="text-warning">{props.blame.issue.rule[0].fullDescription} </span></div>
                <div className="">Severity: <span className="text-warning">{props.blame.issue.rule[0]["security-severity"]} </span></div>
                <div className="">Author: <span className="text-warning">{props.blame.blame.author_name} ({props.blame.blame.author_email})</span></div>
                <div className="">Commit: <span className="text-warning">{props.blame.blame.commit_oid}</span></div>
                <div className="">AI Assistant: </div>
                <div className="bg-black bg-opacity-25 rounded mb-1">
                  Explanation:
                </div>
                <div className="bg-black bg-opacity-25 rounded">
                  Suggestion:
                </div>
                <Button
                  variant="outline-secondary mt-2"
                  size="sm"
                  onClick={() => {
                    setExpand(-1);
                  }}
                >
                  Collapse
                </Button>
              </div>
            ) : (
              ""
            )}
          </>
        </div>
      )),
    [codeString, highlights, expand]
  );

  const languageOptions = useMemo(
    () =>
      SyntaxHighlighter.supportedLanguages.map((language) => (
        <option key={language} value={language}>
          {language}
        </option>
      )),
    []
  );

  return (
    <div className="border rounded p-2 position-relative">
      {loading ? (
        <Spinner animation="border" />
      ) : (
        <>
          <div
            className="position-absolute top-0 start-50 my-1 jump-to-issue"
            onClick={scrollToSection}
          >
            Jump to issue
          </div>
          <CloseButton
            className="end-0 position-absolute mx-2"
            onClick={() => {
              props.setBlame(null);
            }}
          />
            <Form.Select
                className="mb-2 w-50"
                onChange={(e) => setLanguage(e.target.value)}
                value={language}
                >
                {languageOptions}
            </Form.Select>
          {highlightedBlocks}
        </>
      )}
    </div>
  );
};

export default CodePanel;
