import React from 'react';
import PropTypes from 'prop-types';
import * as DataDisplayComponents from './DataDisplayComponents';
import { EndpointEnum } from './Endpoints';

export class BasicResponseDisplayComponent extends React.Component {

  static propTypes = {
    response: PropTypes.shape({
      success: PropTypes.bool.isRequired,
      message: PropTypes.string, // optional
      data: PropTypes.any, // optional
    }),
    endpointType: PropTypes.string,
  };
  
  render() {
    const response = this.props.response;
    const endpointType = this.props.endpointType;

    if (response === null) {
      return (
        <div>no information received yet</div>
      );
    }

    let dataElem;
    // switch rendering based on type
    switch (endpointType) {
      case EndpointEnum.TEST:
        dataElem = <DataDisplayComponents.TestDataDisplayComponent data={response.data}/>;
        break;
      case EndpointEnum.ACCOUNT:
        dataElem = <DataDisplayComponents.AccountDataDisplayComponent data={response.data} />;
        break;
      case EndpointEnum.POWER:
        dataElem = <DataDisplayComponents.PowerDataDisplayComponent data={response.data} />;
        break;
      case EndpointEnum.RAW: // fall through!!!
      default:
        if (response.data === null || Object.keys(response.data).length == 0) { // if data is null or empty
          dataElem = <div>(null or empty)</div>;
        } else {
          dataElem = <div>{JSON.stringify(response.data)}</div>;
        }
        break;
    }

    return ( // TODO: replace <br>'s with css spacing
      <div className="response-display-component">
        success: {JSON.stringify(response.success)}
        <br></br>
        message: {response.message ? '"' + response.message + '"' : '(null)'}
        <br></br>
        data (render type: {this.props.endpointType}): {dataElem /* <-- this is a new div */}
      </div>
    );
  }
}