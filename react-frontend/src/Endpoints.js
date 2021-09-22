
import { CustomEntryComponent } from './CustomEntryComponent';
import React from 'react';
import { EndpointComponent } from './EndpointComponent';

export const EndpointEnum = {
  RAW: 'RAW',
  TEST: 'TEST',
  ACCOUNT: 'ACCOUNT',
  POWER: 'POWER'
}

export const ActionEnum = {
  SIMPLE_GET: 'SIMPLE_GET',
  TEST_POST: 'TEST_POST'
}

export function getActions(endpoint) {
  switch (endpoint) {
    case EndpointEnum.TEST:
      return [ActionEnum.SIMPLE_GET, ActionEnum.TEST_POST];
    default:
      // TODO: maybe `throw new Error()`?
      console.log('ERROR: Endpoint "' + endpoint + "' has no associated Actions!");
      return [ActionEnum.SIMPLE_GET];
  }
}

/* eslint-disable react/jsx-key */
// because these jsx components will not actually be siblings
const rawComponents = [
  <CustomEntryComponent></CustomEntryComponent>,
  // <EndpointComponent endpointURL="/api/endpoints"    endpointType={EndpointEnum.RAW}/>,
  // <EndpointComponent endpointURL="/api/account"      endpointType={EndpointEnum.ACCOUNT}/>,
  // <EndpointComponent endpointURL="/api/main/mc"      endpointType={EndpointEnum.RAW}/>,
  <EndpointComponent endpointURL="/api/test"         endpointType={EndpointEnum.TEST} />,
  // <EndpointComponent endpointURL="/api/power"        endpointType={EndpointEnum.POWER} />,
];

// array of JSX React Components
export const ENDPOINTS = [];

for (let i = 0; i < rawComponents.length; i++) {
  let component = rawComponents[i];
  ENDPOINTS.push(<div className="endpoint-container" key={i}>{component}</div>);
  ENDPOINTS.push(<br key={-i-1}></br>); // TODO: replace this with a css spacing below #endpoint-container
}