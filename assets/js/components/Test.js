/**
 * Test.js: This component is used to test API calls. Change {testFunc} to
 * take the proper arguments for whichever action you want to test. Look at
 * [/js/actions/index.js] for the API functions. The output will be logged to
 * the console. You must be an authenticated user to test the API calls
 * (except for generateInsuranceQuotes).
 */

import React from 'react';
import { connect } from 'react-redux';

import Menu from './Menu';
import Actions from '../actions';
import { isAuthenticated } from '../auth';

class Test extends React.Component {
  componentWillMount() {
    if (isAuthenticated()) {
      this.props.loadUserData();
    }
  }

  handleAPIclick = () => {
    // Pass in the correct function arguments here
    this.props.testFunc(
      // data....
    );
  }

  render() {
    return (
      <div>
        <Menu history={this.props.history} />
        <h1>API Test Componenet</h1>
        <button onClick={this.handleAPIclick}>Make API Call</button>
        <br/><br/>
      </div>
    );
  }
}

const mapDispatchToProps = (dispatch) => ({
  loadUserData: () => dispatch(Actions.fetchUserInfo()),
  // Choose which API function to test here
  testFunc: () => dispatch(Actions.fetchAllInsuranceInfo())
});

export default connect(state => state.app, mapDispatchToProps)(Test);
