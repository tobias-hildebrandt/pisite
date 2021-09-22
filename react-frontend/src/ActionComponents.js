import React from 'react';
import PropTypes from 'prop-types';
import { ActionEnum } from './Endpoints';

function customFetch(url, options, successCallback, failureCallback) {
  fetch(url, options)
  .then(res => res.json())
  .then(
    (result) => {
      successCallback(result)
    },
    (error) => {
      failureCallback(error)
    }
  ).catch(
    error => console.log(error)
  );
}

function customFetch2(url, options, updateActionStateCallback, actionType) {
  fetch(url, options)
  .then(res => res.json())
  .then(
    (result) => {
      updateActionStateCallback(actionType, {
        isLoaded: true,
        response: result
      });
    },
    (error) => {
      updateActionStateCallback(actionType, {
        isLoaded: true,
        error
      });
    }
  ).catch(
    error => console.log(error)
  );
}

export class SimpleGetAction extends React.Component {

  static propTypes = {
    actionState: PropTypes.shape({
      error: PropTypes.any,
      isLoaded: PropTypes.bool,
      response: PropTypes.any,
    }),
    endpointType: PropTypes.string,
    endpointURL: PropTypes.string,
    updateActionState: PropTypes.func,
  };

  doFetch() {
    let endpoint = this.props.endpointURL;
    console.log("fetching endpoint (GET): " + endpoint)
    fetch(endpoint)
    .then(res => res.json())
    .then(
      (result) => {
        this.props.updateActionState(ActionEnum.SIMPLE_GET, {
          isLoaded: true,
          response: result
        });
      },
      (error) => {
        this.props.updateActionState(ActionEnum.SIMPLE_GET, {
          isLoaded: true,
          error
        });
      }
    )
    .catch(
      error => console.log(error)
    )
  }

  render() {
    return (
      <div>
        <button onClick={() => this.doFetch()}>do simple get</button>
        RESPONSE: {JSON.stringify(this.props.actionState.response)}
      </div>
    );
  }
}

export class TestPostAction extends React.Component {

  static propTypes = {
    actionState: PropTypes.shape({
      error: PropTypes.any,
      isLoaded: PropTypes.bool,
      response: PropTypes.any,
    }),
    endpointType: PropTypes.string,
    endpointURL: PropTypes.string,
    updateActionState: PropTypes.func,
  };

  doFetch() {
    // customFetch(this.props.endpointURL, {method: 'POST'},
    //   (result) => {
    //     this.props.updateActionState(ActionEnum.TEST_POST, {
    //       isLoaded: true,
    //       response: result
    //     });
    //   },
    //   (error) => {
    //     this.props.updateActionState(ActionEnum.TEST_POST, {
    //       isLoaded: true,
    //       error
    //     });
    //   }
    // );
    customFetch2(this.props.endpointURL, 
      {
        method: 'POST', 
        body: JSON.stringify(
          {test: "this is a test"},
        )
      }, 
      this.props.updateActionState, 
      ActionEnum.TEST_POST);
    alert("sent test post");
  }

  render() {
    return (
      <div>
        <button onClick={() => this.doFetch()}>do simple post</button>
        RESPONSE: {JSON.stringify(this.props.actionState.response)}
      </div>
    );
  }
}