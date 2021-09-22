import React from 'react';
import PropTypes from 'prop-types';

export class TestDataDisplayComponent extends React.Component {

  static propTypes = {
    data: PropTypes.shape({
        this_was_a_get: PropTypes.bool.isRequired,
        utc_time: PropTypes.string.isRequired,
    })
  };
  
  render() {
    const data = this.props.data;
    return (
      <div className="data-display-component test-data-display-component"> {/*TODO: is the secondary class even necessary?*/}
        was this a GET? {data.this_was_a_get ? "yea" : "naw"}
        <br></br>
        UTC Time: {data.utc_time}
      </div>
    );
  }
}

export class AccountDataDisplayComponent extends React.Component {
  static propTypes = {
    data: PropTypes.shape({
      username: PropTypes.string.isRequired
    })
  };

  render() {
    const data = this.props.data;
    return (
      <div className="data-display-component">
        your account username is: {data.username}
      </div>
    );
  }
}

export class PowerDataDisplayComponent extends React.Component {
  static propTypes = {
    data: PropTypes.shape({
      any_power: PropTypes.bool.isRequired,
      statuses: PropTypes.shape({
        pingable: PropTypes.bool.isRequired,
        connectable: PropTypes.bool.isRequired,
      }),
      info: PropTypes.any,
    })
  };

  render() {
    const data = this.props.data;
    return (
      <div className="data-display-component">
        power status: {data.any_power ? "power is on" : "power is off"}
        <br></br>
        details: {data.statuses.pingable ? "pingable" : "not pingable"}, {data.statuses.connectable ? "connectable" : "not connectable"}
        <br></br>
        info: {JSON.stringify(data.info) /* TODO: flesh this out, need some other flag for type of power status */}
      </div>
    )
  }
}