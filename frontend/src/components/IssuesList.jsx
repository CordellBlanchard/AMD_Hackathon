// Desc: Component to list all the issues from the database
import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { Button, Form, Row, Col, Badge } from "react-bootstrap";

const IssuesList = (props) => {
  const [issues, setIssues] = useState([]);
  const [filter, setFilter] = useState("");
  const [hideResolved, setHideResolved] = useState(false);

  // filter issues based on search term and hideResolved flag
  const filteredIssues = useMemo(() => {
    if (filter === "" && !hideResolved) {
      return issues;
    }
    const filtered = issues.filter((issue) => {
      if (issue.rule[0].name.toLowerCase().includes(filter.toLowerCase())) {
        return true;
      }
      for (const blame of issue.blames) {
        if (blame.file.toLowerCase().includes(filter.toLowerCase())) {
          return true;
        }
      }
      return false;
    });
    if (hideResolved) {
      return filtered.filter((issue) => !issue.resolved);
    }
    return filtered;
  }, [issues, filter, hideResolved]);

  useEffect(() => {
    const fetchIssues = async () => {
      const { data } = await axios.get("http://localhost:5000/list");
      setIssues(data);
      console.log(data);
    };
    fetchIssues();
  }, []);

  const renderIssues = () =>
    filteredIssues.map((issue) => (
      <div className="border p-2 m-2 rounded">
        <Badge
          className="float-end"
          bg={issue.resolved ? "success" : "danger"}
        >
          {issue.resolved ? "Resolved" : "Active"}
        </Badge>
        <div className="text-start mb-2 text-warning">{issue.rule[0].name}</div>
        {issue.blames.map((blame) => (
          <div
            className="border rounded p-2 bg-black bg-opacity-25 text-nowrap blamelist text-truncate text-end blame-box"
            onClick={() => props.setBlame({ issue: issue, blame: blame })}
          >
            <span>
              {blame.file}: {blame.starting_line}
            </span>
          </div>
        ))}
      </div>
    ));

  return (
    <div className="sticky-top">
            {
      props.activeTab === "Issues" ? (<div>
      <div className="mb-2">
        <Row>
          <Col sm="2">
            <Form.Label className="me-2">Search: </Form.Label>
          </Col>
          <Col>
            <Form.Control
              onChange={(e) => {
                setFilter(e.target.value);
                console.log(e.target.value);
              }}
              className="py-0"
            />
          </Col>
          <Col>
            <Form.Check
              type="switch"
              className="text-small mt-1"
              label="Hide resolved"
              checked={hideResolved}
              onChange={(e) => setHideResolved(e.target.checked)}
            />
          </Col>
        </Row>
      </div>

      <div
        className="d-flex flex-column bg-black bg-opacity-10 rounded"
        style={{ maxHeight: "calc(100vh - 200px)", overflowY: "auto" }}
      >
        {renderIssues()}
      </div>
      </div>) : ""}
    </div>
  );
};

export default IssuesList;
