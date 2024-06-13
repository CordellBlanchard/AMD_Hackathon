// WIP list by authors
import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { Button, Form, Row, Col, Badge } from "react-bootstrap";

const AuthorsList = (props) => {
  const [authors, setAuthors] = useState([]);
  const [filter, setFilter] = useState("");


  // filter issues based on search term and hideResolved flag
  const filteredAuthors = useMemo(() => {
    if (filter === "") {
      return authors;
    }
    const filtered = authors.filter((author) => {
      if (author.name.toLowerCase().includes(filter.toLowerCase())) {
        return true;
      }
      for (const blame of author.blames) {
        if (blame.file.toLowerCase().includes(filter.toLowerCase())) {
          return true;
        }
      }
      return false;
    });
    return filtered;
  }, [authors, filter]);

  useEffect(() => {
    const fetchAuthors = async () => {
      const { data } = await axios.get("http://localhost:5000/group_issues?group_by=author_name");
      const mapped_data = Object.keys(data).map((key) => ({"name": key, "issue":data[key], "blames": data[key][0]["blames"]}))
      setAuthors(mapped_data);
      console.log("authors")
      console.log(mapped_data);
    };
    fetchAuthors();
  }, []);

  const renderAuthors = () =>
    filteredAuthors.map((author) => (
      <div className="border p-2 m-2 rounded">
        <Badge
          className="float-end"
          bg={author.issue.resolved ? "success" : "danger"}
        >
          {author.issue.resolved ? "Resolved" : "Active"}
        </Badge>
        <div className="text-start mb-2 text-warning">{author.name}</div>
        {author.issue.blames.map((blame) => (
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
      props.activeTab === "Authors" ? (<div><div className="mb-2">
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
        </Row>
      </div>

      <div
        className="d-flex flex-column bg-black bg-opacity-10 rounded"
        style={{ maxHeight: "calc(100vh - 200px)", overflowY: "auto" }}
      >
        {renderIssues()}
      </div></div>) : ""
    }
      
    </div>
  );
};

export default AuthorsList;
