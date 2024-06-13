import { useMemo } from 'react';
import {Button, Form, ButtonGroup} from 'react-bootstrap';


function NavigationTabs(props) {
  const labels = ["Issues", "Rules", "Files", "Authors"];
  const buttons = useMemo(() => labels.map((label) => (
    <Button
      key={label}
      variant={label === props.activeTab ? "secondary" : "outline-secondary"}
      onClick={() => props.setActiveTab(label)}
    >
      {label}
    </Button>
  )), [labels, props]);

  return (
    <div className="mb-2">
      <ButtonGroup aria-label="Navigation tabs" >
        {buttons}
      </ButtonGroup>

    </div>
  );
}

export default NavigationTabs;