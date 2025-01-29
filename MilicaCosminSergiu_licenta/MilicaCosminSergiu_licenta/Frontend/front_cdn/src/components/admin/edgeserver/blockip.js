import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './blockip.css';
import AWS from 'aws-sdk';

AWS.config.update({
  region: 'eu-central-1', 
  accessKeyId: '',
  secretAccessKey: '', 
});
const ec2 = new AWS.EC2();

const BlockedIpsList = () => {
  const [blockedIps, setBlockedIps] = useState([]);
  const [selectedIps, setSelectedIps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ip, setIP] = useState('');
  const token = localStorage.getItem('token');
  const storedIP = sessionStorage.getItem('ec2Ip');
  const DdosIP = sessionStorage.getItem('ec2Ddos');
  useEffect(() => {
    const DdosIP = sessionStorage.getItem('ec2Ddos');
    if (DdosIP) {
      setIP(DdosIP);
      setLoading(false);
    } else {
      const params = {
        InstanceIds: ['i-08ad270f48e7adec9'],
      };

      ec2.describeInstances(params, (err, data) => {
        if (err) {
          console.log("Error", err);
        } else {
          const instance = data.Reservations[0].Instances[0];
          const publicIP = instance.PublicIpAddress || 'No Public IP assigned';
          setIP(publicIP);
          sessionStorage.setItem('ec2Ddos', publicIP);
          setLoading(false);
        }
      });
    }
  }, []);
  useEffect(() => {
    const fetchBlockedIps = async () => {
      try {
        const response = await axios.get(`http://${storedIP}/api/cdn/edgeserver_service/banip`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setBlockedIps(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBlockedIps();
  }, [token]);

  const handleCheckboxChange = (ip) => {
    setSelectedIps((prevSelectedIps) =>
      prevSelectedIps.includes(ip)
        ? prevSelectedIps.filter((selectedIp) => selectedIp !== ip)
        : [...prevSelectedIps, ip]
    );
  };

  const handleUnban = async () => {
    try {
      const response = await axios.post(
        `http://${DdosIP}/api/banmanager/unban`,
        { ip_addresses: selectedIps },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      alert('Unban request sent successfully');
      setBlockedIps((prevBlockedIps) => 
        prevBlockedIps.filter(ip => !selectedIps.includes(ip.ip_address))
      );
      setSelectedIps([]);
    } catch (err) {
      alert(`Error sending unban request: ${err.message}`);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="containerip">
      <h1>Blocked IPs</h1>
      <div className="ips-container">
        {blockedIps.map((ip, index) => (
          <div key={index} className="ip-block">
            <div className="ip-info">
              <p><strong>IP Address:</strong> {ip.ip_address}</p>
              <p><strong>Blocked At:</strong> {ip.blocked_at}</p>
            </div>
            <input
              type="checkbox"
              checked={selectedIps.includes(ip.ip_address)}
              onChange={() => handleCheckboxChange(ip.ip_address)}
            />
          </div>
        ))}
      </div>
      <button onClick={handleUnban} disabled={selectedIps.length === 0}>
        Unban Selected IPs
      </button>
    </div>
  );
};

export default BlockedIpsList;
