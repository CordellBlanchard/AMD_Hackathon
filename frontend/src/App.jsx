import { useState } from "react";
import "./App.css";
import IssuesList from "./components/IssuesList";
import NavigationTabs from "./components/NavigationTabs";
import CodePanel from "./components/CodePanel";
import { Col, Row } from "react-bootstrap";
import { Container } from "react-bootstrap";
import AuthorsList from "./components/AuthorsList";

function App() {
  const [activeTab, setActiveTab] = useState("Issues");
  const [blame, setBlame] = useState(null);

  return (
    <>
      <h3>CodeQL Detective</h3>
      <NavigationTabs activeTab={activeTab} setActiveTab={setActiveTab} />
        <Row className="flex-nowrap">
          <Col sm={blame ? "4" : null}>
            <IssuesList setBlame={setBlame} blame={blame} activeTab={activeTab} />

          </Col>
          {blame !== null ? (
            <Col>
              <CodePanel setBlame={setBlame} blame={blame} />
            </Col>
          ) : (
            ""
          )}
        </Row>
    </>
  );
}

export default App;
