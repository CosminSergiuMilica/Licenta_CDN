import { useNavigate } from 'react-router-dom';
import './home.css';
import React, { useEffect, useState } from 'react';
import AWS from 'aws-sdk';

AWS.config.update({
  region: 'eu-central-1', 
  accessKeyId: '',
  secretAccessKey: '', 
});
const ec2 = new AWS.EC2();

function Home() {
  const navigate = useNavigate();
  const [ip, setIP] = useState('');
  const [loading, setLoading] = useState(true);
  const redirectToSiteAdd = () => {
    navigate('/add_site');
  };
  
  useEffect(() => {
    const storedIP = sessionStorage.getItem('ec2Ip');
    if (storedIP) {
      setIP(storedIP);
      setLoading(false);
    } else {
      const params = {
        InstanceIds: ['i-034bec8cfe1190a43'],
      };

      ec2.describeInstances(params, (err, data) => {
        if (err) {
          console.log("Error", err);
        } else {
          const instance = data.Reservations[0].Instances[0];
          const publicIP = instance.PublicIpAddress || 'No Public IP assigned';
          setIP(publicIP);
          sessionStorage.setItem('ec2Ip', publicIP);
          setLoading(false);
        }
      });
    }
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div className="text">
        <h1 className="main-header">CDN TUIASI</h1>
        <h3 className="sub-header">Înainte de a începe vă recomandăm să citiți despre platformă și modul în care vă ajută să aduceți experiențe mai bune clienților.</h3>
        <h2> Alegeți planul care se potriveste nevoilor dumneavoastră.</h2>
        <div>
          <h3>Ce este un CDN?</h3>
          <p>O rețea de distribuire a conținutului (CDN) este o rețea de servere distribuite geografic care lucrează împreună pentru a livra conținutul de pe internet rapid și eficient. CDNs îmbunătățesc performanța site-urilor web prin reducerea latenței și creșterea vitezei de încărcare a paginilor.</p>
          <p>Prin utilizarea unui CDN, conținutul static, cum ar fi fișierele JavaScript, foile de stil CSS, imagini și videoclipuri, sunt distribuite de pe serverele cele mai apropiate de utilizatorii finali. Acest lucru nu doar îmbunătățește experiența utilizatorului, dar și reduce încărcarea pe serverele originare și îmbunătățește securitatea site-ului.</p>
        </div>
        <div className="categories">
          <div className="category" onClick={redirectToSiteAdd}>
            <h2>Basic</h2>
            <p>Dimensiunea maxima a fisierelor stocate: 1mb</p>
            <p>Permiterea alegerii tipului de resurse stocate in retea</p>
            <p>Alegerea timpului in care resursa sa fie stocata in retea</p>
            <p>Stergerea resurselor de pe serverele noastre</p>
          </div>
          <div className="category" onClick={redirectToSiteAdd}>
            <h2>Advanced</h2>
            <p>Dimensiunea maxima a fisierelor stocate: 5mb</p>
            <p>Permiterea alegerii tipului de resurse stocate in retea</p>
            <p>Alegerea timpului in care resursa sa fie stocata in retea</p>
            <p>Mod development: platforma returneaza doar raspunsuri de la origine pentru a avea continut cat mai actualizat </p>
            <p>Stergerea resurselor de pe serverele noastre</p>
          </div>
          <div className="category" onClick={redirectToSiteAdd}>
            <h2>Enterprise</h2>
            <p>Dimensiunea maxima a fisierelor stocate: 10Mb</p>
            <p>Permiterea alegerii tipului de resurse stocate in retea</p>
            <p>Alegerea timpului in care resursa sa fie stocata in retea</p>
            <p>Mod development: platforma returneaza doar raspunsuri de la origine pentru a avea continut cat mai actualizat</p>
            <p>Stergerea resurselor de pe serverele noastre</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;