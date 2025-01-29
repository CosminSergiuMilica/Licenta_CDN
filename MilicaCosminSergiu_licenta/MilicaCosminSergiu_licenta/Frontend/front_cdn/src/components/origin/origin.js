import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import "./origin.css";

function MySiteComponent() {
  const [originServiceData, setOriginServiceData] = useState(null);
  const [modeDevelopmentChecked, setModeDevelopmentChecked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { domain } = useParams();
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [message, setMessage] = useState('');

  const [updateData, setUpdateData] = useState({
    ip: '',
    type_plan: '',
    time_cache: '',
    resource_static: ''
  });
  const navigate = useNavigate(); 
  const token = localStorage.getItem('token');
  const storedIP = sessionStorage.getItem('ec2Ip');
  useEffect(() => {
      const userRole = localStorage.getItem('userRole');
      if (userRole !== 'user') {
        navigate('/'); 
      }
  }, [navigate]);
  
  useEffect(() => {
    const fetchOriginServiceData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`http://${storedIP}/api/cdn/origin_service/${domain}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setOriginServiceData(response.data);
        setUpdateData({
          ip: response.data.ip || '',
          type_plan: response.data.type_plan || '',
          time_cache: response.data.time_cache || '',
          resource_static: response.data.resource_static || []
        });
        setModeDevelopmentChecked(response.data.mode_development || false);
        const planOriginResponse = await axios.get(`http://${storedIP}/api/cdn/origin_service/plan/${domain}`, {
          headers: {
          Authorization: `Bearer ${token}`,
          },
        });
        const planOriginData = planOriginResponse.data.plan;

        setOriginServiceData(prevData => ({
          ...prevData,
          planOriginData: planOriginData,
        }));
        setLoading(false);
      } catch (error) {
        if (error.response && error.response.status === 401) {
          navigate('/logout');
        } else {
          setError(error.message);
          setLoading(false);
        }
      }
    };

    fetchOriginServiceData();
  }, [domain, navigate]); 

  const handleModeDevelopmentChange = async (event) => {
    const newModeDevelopmentValue = event.target.checked;
    try {

      await axios.patch(`http://${storedIP}/api/cdn/origin_service/mode_dev/${domain}`, {
        mode_development: newModeDevelopmentValue,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setOriginServiceData(prevData => ({
        ...prevData,
        mode_development: newModeDevelopmentValue,
      }));
      setModeDevelopmentChecked(prev => !prev);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        navigate('/logout');
      } else {
        setError(error.message);
        setLoading(false);
      }
    }
  };
  const handleUpdateFormToggle = () => {
    setShowUpdateForm(!showUpdateForm);
  };
  const redirectToCachePage = () => {
    navigate(`/cache/${domain}`);
  };

  const handleDeleteSite = async () => {
    const confirmDelete = window.confirm("Ești sigur că vrei să ștergi acest site?");
    if (confirmDelete) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`http://${storedIP}/api/cdn/origin_service/${domain}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        navigate('/my-sites'); 
      } catch (error) {
        if (error.response && error.response.status === 401) {
          navigate('/logout');
        } else {
          setError(error.message);
        }
      }
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!originServiceData) {
    return <div>No data available</div>;
  }
  const handleChange = (event) => {
    const { name, value } = event.target;
    setUpdateData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setMessage('');
  setError('');

  if (!updateData || !updateData.ip || !updateData.type_plan) {
    setError("Datele necesare nu sunt complet definite.");
    return;
  }

  try {
    const response = await axios.put(`http://${storedIP}/api/cdn/origin_service/${domain}`, updateData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    setMessage(response.data.message);
    setOriginServiceData({ ...originServiceData, ...updateData });  
  } catch (err) {
    if (err.response && err.response.status === 401) {
      navigate('/logout');
    } else {
      setError(err.response ? err.response.data.message : "A apărut o eroare la server.");
    }
  }
};
const handleTimeCacheChange = (e) => {
    setUpdateData({ ...updateData, time_cache: e.target.value });
  };

const handleCheckboxChange = (e) => {
    const { value, checked } = e.target;
    setUpdateData(prevState => ({
      ...prevState,
      resource_static: checked ? [...prevState.resource_static, value] : prevState.resource_static.filter(option => option !== value)
    }));
  };

const resourceStaticOptions = [
"CSS", "JPG", "JPEG", "JS", "JSON","PDF", "PNG", "PPT", "PPTX", "TXT",  "ZIP", "DOC", "MP4"
];

const UpdateForm = () => (
  <div class="container-origin">
  <div class="form-container-origin">
    <h2>Poti modifica Site-ul tau</h2>
    <form onSubmit={handleSubmit}>
      <label>
        IP:
        <input type="text" name="ip" placeholder='ip' value={updateData.ip} onChange={handleChange} />
      </label>
      <label>
        Tipul Planului:
        <select name="type_plan" value={updateData.type_plan} onChange={handleChange}>
          <option value="basic">Basic</option>
          <option value="advanced">Advanced</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </label>
      <label for="timeInput">Timpul de stocare in retea:</label>
        <select name="time_cache" value={updateData.time_cache}  onChange={handleTimeCacheChange}>
         
          <option value="1h">1h</option>
          <option value="2h">2h</option>
          <option value="3h">3h</option>
          <option value="4h">4h</option>
        </select>
      <label>Resursele statice:</label>
        
      <div class="resource-static-container">
        {resourceStaticOptions.map(option => (
          <label key={option}>
            <input type="checkbox" name="resource_static" checked={updateData.resource_static.includes(option)} value={option} onChange={handleCheckboxChange} />
            {option}
          </label>
        ))}
      </div>
      <div className="message"  style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>
      {error && <div className="error" style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{error}</div>}
      {message && <div className="message" style={{ color: 'green', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>}
      <button type="submit">Update</button>
    </form>
  </div>
</div>
);

  return (
    <div className="container-origin">
      <div className="content">
        <div className="header">
          <h1>Detalii Site</h1>
        </div>
        <div className="details">
          <div className="detail-item">
            <span className="label">Domeniu:</span>
            <span className="value">
              <a href={`http://${originServiceData.domain}`} target="_blank" rel="noopener noreferrer">{originServiceData.domain}</a>
            </span>
          </div>
          <div className="detail-item">
            <span className="label">IP:</span>
            <span className="value">{originServiceData.ip}</span>
          </div>
          <div className="detail-item">
            <span className="label">Timpul de retinere in cache:</span>
            <span className="value">{originServiceData.time_cache}</span>
          </div>
          <div className="detail-item">
            <span className="label">Plan:</span>
            <span className="value">{originServiceData.planOriginData.id}</span>
          </div>
          <div className="detail-item">
            <span className="label">Dimensiune fișier:</span>
            <span className="value">{originServiceData.planOriginData.file_size}</span>
          </div>
          <div className="detail-item">
            <span className="label">Mod dezvoltare:</span>
            <span className="value">{originServiceData.planOriginData.mode_development ? 'Da' : 'Nu'}</span>
          </div>
          {/* <div className="detail-item">
            <span className="label">Mod offline:</span>
            <span className="value">{originServiceData.planOriginData.mode_offline ? 'Da' : 'Nu'}</span>
          </div> */}
          {/* <div className="detail-item">
            <span className="label">Management resurse:</span>
            <span className="value">{originServiceData.planOriginData.managment_resource ? 'Da' : 'Nu'}</span>
          </div> */}

          {originServiceData.planOriginData.mode_development &&
            <div className="checkbox-wrapper-mode">
              <input type="checkbox" id="mode-development" name="mode-development" checked={modeDevelopmentChecked} onChange={handleModeDevelopmentChange} />
              <label htmlFor="mode-development">
                <span></span>Mod Dezvoltare
              </label>
            </div>
          }
            <div>
              {originServiceData.planOriginData.managment_resource && 
              <button className='button managment-resurse' onClick={redirectToCachePage}>Resurse</button>
              }
              <button className='button delete-site' onClick={handleDeleteSite}>Delete Site</button>
              <button className="button update-site" onClick={() => setShowUpdateForm(true)}>Update EdgeServer</button>
              {showUpdateForm && <UpdateForm />}
            </div>
        </div>
      </div>
    </div>
  );
}

export default MySiteComponent;
