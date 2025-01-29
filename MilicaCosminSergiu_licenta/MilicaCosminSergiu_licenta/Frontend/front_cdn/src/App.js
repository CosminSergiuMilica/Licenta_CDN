import { BrowserRouter as Router, Route,Routes } from 'react-router-dom';
import Login from './components/login/login';
import Signup from './components/signup/signup';
import Header from './components/header/header';
import Footer from './components/footer/footer';
import Logout from './components/logout';
import Home from './components/home/home';
import OriginService from './components/origin_add/originadd';
import UserDataComponent from './components/profile/profile';
import OriginServiceComponent from './components/origin-service/originservices';
import MySiteComponent from './components/origin/origin';
import CacheManager from './components/cache_manager/cache_manager'
import AdminRequests from './components/admin/requests/requests';
import AddEdgeService from './components/admin/add_edgeserver/AddEdgeServer';
import EdgeServers from './components/admin/edgeserver/edgeserver';
import IndividualEdgeServer from './components/admin/edgeserver/individualedgeserver';
import BlockedIpsList from './components/admin/edgeserver/blockip';
import './App.css';
function App() {
  return (
    <Router>
      <div>
        <Header />
        <Routes>
          <Route path="/" element={<Home/>} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup/>} />
          <Route path='/logout' element={<Logout/>}/>
          <Route path='/add_site' element={<OriginService/>}/>
          <Route path='/profile' element={<UserDataComponent/>}/>
          <Route path='/my-sites' element={<OriginServiceComponent/>}/>
          <Route path="/my-site/:domain" element={<MySiteComponent/>}/>
          <Route path='/cache/:domain' element={<CacheManager/>}/>
          <Route path='/admin/trafic' element={<AdminRequests/>}/>
          <Route path='/admin/addedge' element={<AddEdgeService/>}/>
          <Route path='/admin/edgeservers' element={<EdgeServers/>}/>
          <Route path='/admin/edgeservers/:instance_id' element={<IndividualEdgeServer/>}/>
          <Route path='/admin/edgeservers/banip' element={<BlockedIpsList/>}/>
        </Routes>
        <Footer/>
      </div>
    </Router>
  );
}

export default App;
