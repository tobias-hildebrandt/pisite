import React from 'react';
import PropTypes from 'prop-types';
import { BasicResponseDisplayComponent } from './BasicResponseDisplayComponent';
import { ActionEnum, EndpointEnum, getActions } from './Endpoints';
import * as ActionComponents from './ActionComponents';

export class EndpointComponent extends React.Component {

  static propTypes = {
    endpointURL: PropTypes.string.isRequired,
    endpointType: PropTypes.string, // TODO: required? (also change in response displays)
  };
  
  constructor(props) {
    super(props);
    this.state = {
      actionStates: {}
    }

    const endpointActions = getActions(this.props.endpointType);

    for (let action of endpointActions) {
      // let newStateToMerge = {};

      // newStateToMerge.actionStates[action] = {
      //   error: null,
      //   isLoaded: false,
      //   response: null
      // };

      // this.setState(newStateToMerge);
      console.log('Endpoint "' + this.props.endpointType + '" has action "' + action + '"')

      this.state.actionStates[action] = {
        error: null,
        isLoaded: false,
        response: null,
      };
    }

    this.updateActionState = this.updateActionState.bind(this); // so that function can be passed via props to children
  }

  updateActionState(action, newActionState) {
    // let newStateToMerge = {
    //   actionStates: {}
    // };
    // newStateToMerge.actionStates[action] = newActionState;

    // console.log('merging new state: ' + JSON.stringify(newStateToMerge));

    this.setState(function(state) { // function taking old state as parameter
      state.actionStates[action] = newActionState;

      return state;
    });

    // this.logState();
  }

  logState() {
    console.log('current state: ' + JSON.stringify(this.state));
  }
  
  render() {
    console.log("render triggered");
    // this.logState();
    
    let vitalInfoElement = <VitalInfoElement endpointType={this.props.endpointType} wholeState={this.state}/>
    //<BasicResponseDisplayComponent response={this.state.response} endpointType={this.props.endpointType} />

    let actionElements = [];

    for (let action of getActions(this.props.endpointType)) {
      let newElem;
      if (!this.state.actionStates[action]) { // actionState has not been set yet
        newElem = (
          <div>actionState for {action} not yet initialized</div>
        );
      }
      else {
        switch(action) {
          case ActionEnum.SIMPLE_GET:
            newElem = (
              <ActionComponents.SimpleGetAction
              actionState={this.state.actionStates[action]}
              endpointType={this.props.endpointType}
              endpointURL={this.props.endpointURL}
              updateActionState={this.updateActionState}
              key={this.props.endpointURL + " " + action}
              />
            );
            break;
          case ActionEnum.TEST_POST:
            newElem = (
              <ActionComponents.TestPostAction
              actionState={this.state.actionStates[action]}
              endpointType={this.props.endpointType}
              endpointURL={this.props.endpointURL}
              updateActionState={this.updateActionState}
              key={this.props.endpointURL + " " + action}
              />
            );
            break;
          default:
            newElem = (
              <div key={this.props.endpointURL + " " + action}>unimplemented for action {action}</div>
            );
            break;
        }
      }
      
      actionElements.push(newElem);
    }
    
    return (
      <div className="simple-get-comp" id={this.props.endpointURL}>
        <div>ENDPOINT {this.props.endpointType}, {this.props.endpointURL}</div>
        {actionElements}
        {vitalInfoElement}
      </div>
    );
  }
}

export class VitalInfoElement extends React.Component {
  static propTypes = {
    endpointType: PropTypes.string,
    wholeState: PropTypes.any, // readonly
  };

  render() {
    if (this.props.wholeState == undefined || this.props.wholeState == null) {
      return <div>state not yet initilized</div>;
    }
    switch (this.props.endpointType) {
      case EndpointEnum.TEST:
        return (
          <div>vital stringified: {JSON.stringify(this.props.wholeState.actionStates[ActionEnum.SIMPLE_GET])}</div>
        );
      default:
        console.log('IN VitalInfoElement: endpoint type "' + this.props.endpointType + '" not implemented');
        return <div>wholestate stringified: {JSON.stringify(this.wholeState)}</div>;
    }
  }
}