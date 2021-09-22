import React from 'react';

export class CustomEntryComponent extends React.Component {
  
  constructor(props) {
    super(props);
    this.state = {
      error: null,
      isLoaded: false,
      response: null,
      targetEndpoint: '/api/test',
    }
    
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  toString() {
    return "Test Component"
  }
  
  doTestFetch() {
    this.doTargetedFetch('/api/test');
  }
  
  doTargetedFetch(endpoint) {
    console.log("fetching endpoint: " + endpoint)
    fetch(endpoint)
    .then(res => res.json())
    .then(
      (result) => {
        this.setState({
          isLoaded: true,
          response: result
        });
      },
      (error) => {
        this.setState({
          isLoaded: true,
          error
        });
      }
    )
    .catch(
      error => console.log(error)
      )
    }
      
  handleSubmit(event) {
    this.doTargetedFetch(this.state.targetEndpoint);
    event.preventDefault();
  }
  
  handleChange(event) {
    // console.log('target value: ', event.target.value);
    this.setState({
      targetEndpoint: event.target.value
    });
  }
  
  render() {
    let statusElem;
    
    if (this.state.error) {
      statusElem = <div>Error: {this.state.error.message}</div>
    } else if (!this.state.isLoaded) {
      statusElem = <div>Not yet sent request</div>
    } else {
      statusElem = <div>stringified response: {JSON.stringify(this.state.response)}</div>
    }
    
    // `() => this.thing()` to avoid having to bind in constructor
    // <button onClick={() => this.doTestFetch()}>this is the test button</button>
    return (
      <div className="test-comp">
        <form onSubmit={this.handleSubmit}>
          <label>
            Endpoint:
            <input type="text" value={this.state.targetEndpoint} onChange={this.handleChange}/>
          </label>
          <input type="submit" value="Submit"></input>
        </form>
        {statusElem}
      </div>
    )
  }
}