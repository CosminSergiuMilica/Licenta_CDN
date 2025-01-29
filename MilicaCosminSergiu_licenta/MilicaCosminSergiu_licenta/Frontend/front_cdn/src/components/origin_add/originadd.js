import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './originadd.css';

function OriginService() {
  const [originData, setOriginData] = useState({
    owner: '',
    domain: '',
    ip: '',
    type_plan: '',
    time_cache: '',
    resource_static: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate(); 
  const storedIP = sessionStorage.getItem('ec2Ip');
    
  useEffect(() => {
      const userRole = localStorage.getItem('userRole');
      if (userRole !== 'user') {
        navigate('/'); 
      }
  }, [navigate]);

  useEffect(() => {
    
    const owner = localStorage.getItem('userId');
    setOriginData(prevState => ({ ...prevState, owner }));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { owner, domain, ip, type_plan, time_cache, resource_static } = originData;
    if (!owner || !domain || !ip || !type_plan || !time_cache || resource_static.length === 0) {
      setMessage("Toate câmpurile sunt obligatorii.");
      return;
    }

    const sensitiveCharsRegex = /[<>&#]/;
    if (sensitiveCharsRegex.test(domain)) {
      setError("Domeniul nu poate contine caractere sensibile (<, >, & sau #).");
      return;
    }
    const ipv4Regex = /^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$/;
    if (!ipv4Regex.test(ip)) {
      setError("Adresa IP trebuie să fie o adresă IPv4 validă.");
      return;
    }
    const timeCacheRegex = /^[0-9]{1,2}h$/;
    if (!timeCacheRegex.test(time_cache)) {
      setError("Timpul de stocare trebuie sa fie format din maxim doua cifre urmate de litera 'h'. Exemplu: 2h");
      return;
    }

    const token = localStorage.getItem('token');
    try {
      const response = await axios.post(`http://${storedIP}/api/cdn/origin_service/`, originData, {
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

  const handleCheckboxChange = (e) => {
    const { value, checked } = e.target;
    setOriginData(prevState => ({
      ...prevState,
      resource_static: checked ? [...prevState.resource_static, value] : prevState.resource_static.filter(option => option !== value)
    }));
  };

  const handleChange = (e) => {
    setOriginData({ ...originData, [e.target.name]: e.target.value });
  };

  const handleTimeCacheChange = (e) => {
    setOriginData({ ...originData, time_cache: e.target.value });
  };

  return (
  <div class="container-origin">
  <div class="form-container-origin">
    <h2>Adauga site-ul tau aici</h2>
    <form onSubmit={handleSubmit}>
      <label>
        Domain:
        <input type="text" name="domain" placeholder='domain' onChange={handleChange} />
      </label>
      <label>
        IP:
        <input type="text" name="ip" placeholder='ip' onChange={handleChange} />
      </label>
      <label>
        Tipul Planului:
        <select name="type_plan" onChange={handleChange}>
          <option value="">Select Type Plan</option>
          <option value="basic">Basic</option>
          <option value="advanced">Advanced</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </label>
      <label for="timeInput">Timpul de stocare in retea:</label>
        {/* <input type="text" id="timeInput" placeholder='h-ore m-minute s-secunde ex:2h ' name="time_cache" onChange={handleTimeCacheChange}></input> */}
        <select name="time_cache"  onChange={handleTimeCacheChange}>
         
          <option value="1h">1h</option>
          <option value="2h">2h</option>
          <option value="3h">3h</option>
          <option value="4h">4h</option>
        </select>
      <label>Resursele statice:</label>
        
      <div class="resource-static-container">
        {resourceStaticOptions.map(option => (
          <label key={option}>
            <input type="checkbox" name="resource_static" value={option} onChange={handleCheckboxChange} />
            {option}
          </label>
        ))}
      </div>
      <div className="message"  style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>
      {error && <div className="error" style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{error}</div>}
      {message && <div className="message" style={{ color: 'green', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>}
      <button type="submit">Adauga Site</button>
    </form>
  </div>
</div>

  );
};

const resourceStaticOptions = [
"CSS", "JPG", "JPEG", "JS", "JSON","PDF", "PNG", "PPT", "PPTX", "TXT",  "ZIP", "DOC", "MP4"
];

// [
//   "7Z", "AVI", "AVIF", "APK", "BIN", "BMP", "BZ2",
//   "CLASS", "CSS", "CSV", "DOC", "DOCX", "DMG", "EJS",
//   "EPS", "EXE", "FLAC", "GIF", "GZ", "ICO", "ISO",
//   "JAR", "JPG", "JPEG", "JS", "JSON", "MID", "MIDI",
//   "MKV", "MP3", "MP4", "OGG", "PDF", "PICT", "PLS",
//   "PNG", "PPT", "PPTX", "PS", "RAR", "SVG", "SVGZ",
//   "SWF", "TAR", "TIFF", "TIF", "TTF", "TXT", "WAV",
//   "WEBM", "WEBP", "WOFF", "WOFF2", "XLS", "XLSX",
//   "ZIP", "ZST"
// ];

export default OriginService;
