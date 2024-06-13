// Desc: Component to list all the issues from the database
import React, { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "react-bootstrap";

const IssuesList = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    const fetchIssues = async () => {
      const { data } = await axios.get("http://localhost:5000/list");
      setIssues(data);
      console.log(data);
    };
    fetchIssues();
  }, []);

  const renderIssues = () =>
    issues.map((issue) => (
      <div className="border p-2 m-2 rounded">
        <div className="text-start mb-2 text-warning">{issue.rule}</div>
        {issue.blames.map((blame) => (
            <div className="d-flex justify-content-between border rounded p-2 bg-black bg-opacity-25">
                <span>{blame.file} : </span>
                <span>{blame.starting_line}</span>
            </div>
        ))}
      </div>
    ));

  return <div className="d-flex flex-column">{renderIssues()}</div>;
};

export default IssuesList;
