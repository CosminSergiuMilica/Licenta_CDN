import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function AddEdgeService() {
  const [Data, setData] = useState({
    instance_id: '',
    region: '',
    lon: '',
    lat: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate(); 
  const storedIP = sessionStorage.getItem('ec2Ip');
  useEffect(() => {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'admin') {
      navigate('/'); 
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { instance_id, region, lat, lon } = Data;
    if (!instance_id|| !region || !lat || !lon) {
      setMessage("Toate câmpurile sunt obligatorii.");
      return;
    }

    const sensitiveCharsRegex = /[<>&#]/;
    if (sensitiveCharsRegex.test(instance_id)) {
      setError("Datele nu poate contine caractere sensibile (<, >, & sau #).");
      return;
    }
    if (sensitiveCharsRegex.test(region)) {
      setError("Datele nu poate contine caractere sensibile (<, >, & sau #).");
      return;
    }

    const token = localStorage.getItem('token');

    try {
      const response = await axios.post(`http://${storedIP}/api/cdn/edgeserver_service/`, Data, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setMessage(response.data.message);
    } catch (err) {
      if (err.response && err.response.status === 401) {
          
          navigate('/logout');
      } 
      else {
          setError(err.response.data.message);
          
        }
    }
  };

  const handleChange = (e) => {
    console.log(e.target.name, e.target.value);
    e.stopPropagation(); 
    setData({ ...Data, [e.target.name]: e.target.value });
};

  const handleRegionChange = (e) => {
    setData({ ...Data, region: e.target.value });
  };

  return (
    <div class="container-origin">
  <div class="form-container-origin">
    <h2>Adauga un EdgeServer nou</h2>
    <form onSubmit={handleSubmit}>
      <label>
        Region:
        <select name="region"  onChange={handleRegionChange}>
          <option value="us-east-2">Ohio</option>
          <option value="eu-central-1">Frankfurt</option>
          <option value="eu-west-2">London</option>
          <option value="ap-northeast-2">Seoul</option>
          <option value="sa-east-1">Sao Paulo</option>
          <option value="us-west-1">California</option>
        </select>
      </label>
      <label>
        InstanceID:
        <input type="text" name="instance_id" placeholder='instanceID' onChange={handleChange} />
      </label>
      <label>
        Longitudine:
        <input type="float" name="lon" placeholder='longitudine' onChange={handleChange} step="0.0000001" />
    </label>
      <label>
        Latitudine:
        <input type="float" name="lat" placeholder='latitudine' onChange={handleChange} step="0.00000001" />
      </label>
      <div className="message"  style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>
      {error && <div className="error" style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{error}</div>}
      {message && <div className="message" style={{ color: 'green', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>}
      <button type="submit">Adauga EdgeServer</button>
    </form>
  </div>
</div>

  );
};

export default AddEdgeService;
