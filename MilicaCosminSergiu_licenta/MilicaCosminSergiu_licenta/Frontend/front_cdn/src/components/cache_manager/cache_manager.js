import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import './cache_manager.css'

function CacheManager() {
    const [cacheResource, setCacheResouce]= useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedResource, setSelectedResource] = useState('');
    const[error, setError] = useState(null);
    const { domain } = useParams();
    const storedIP = sessionStorage.getItem('ec2Ip');

    const [inCacheChecked, setInCacheChecked] = useState(true);
    const navigate = useNavigate();

    useEffect(()=>{
        const fetchData = async() =>{
            try{
                const token = localStorage.getItem('token');

                const response = await axios.get(`http://${storedIP}/api/cdn/cache_service/redis_cache/${domain}`, {
                    headers:{
                    Authorization: `Bearer ${token}`,
                    },
                });
                setCacheResouce(response.data.keys);
                setLoading(false);
            }
            catch (error){
                if (error.response && error.response.status === 401) {
          
                    navigate('/logout');
                } else {
                    setError(error.message);
                    setLoading(false);
                }
            }
        };
        fetchData();
    },[domain]);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }
    const handleResourceChange = (event) => {
        setSelectedResource(event.target.value);
    };

    const handleDeleteResource = async () => {
        try {
            const newResource = selectedResource.replace(/\//g, ':');
            const token = localStorage.getItem('token');
            await axios.delete(`http://${storedIP}/api/cdn/cache_service/redis_cache/resource/${newResource}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            });
            
        } catch (error) {
            if (error.response && error.response.status === 401) {
                navigate('/logout');
            } else {
                console.error('Error:', error.message);
            }
        }
    };

    const handleDeleteAllCacheData = async () => {
        try{
            const token = localStorage.getItem('token');
            await axios.delete(`http://${storedIP}/api/cdn/cache_service/redis_cache/${domain}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            });
        }
        catch(error){
             if (error.response && error.response.status === 401) {
                navigate('/logout');
            } else {
                console.error('Error:', error.message);
            }
        }
    };

    const handleModifyResource = async () =>{
        try{
            const token = localStorage.getItem('token');
            const data = {
                domain: domain,
                resource: selectedResource,
                time_cache: document.querySelector('.new_time').value,
                in_cache: inCacheChecked
            };
            await axios.put(`http://${storedIP}/api/cdn/cache_service/special_resource/`, data, {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            });
        }catch (error) {
            if (error.response && error.response.status === 401) {
                navigate('/logout');
            } else {
                console.error('Error:', error.message);
            }
        }
           
    };
    const handleCheckboxChange = () => {
        setInCacheChecked(prev => !prev);
    };

return (
        <div className='container-cache'>
            <h1 className="main-header">Your Data</h1>
            <div className="cache-plan">
                <p>Puteți actualiza baza noastră de date prin eliminarea resurselor învechite pentru a asigura informații la zi. 
                De asemenea, aveți posibilitatea de a elimina o resursă din cache, prevenind astfel stocarea ulterioară a acesteia.</p>
            </div>
            <form className='form-cache'>
                <h2>Resurse: {domain}</h2>
                <select className='resource' value={selectedResource} onChange={handleResourceChange}>
                    <option value=''>Selectează o resursă</option>
                    {cacheResource.map((item, index) => (
                    <option key={index} value={item}>{item}</option>
                ))}
                </select>
                <div>
                    <button className="button" onClick={handleDeleteResource} >Șterge Resursa</button>
                    <button className="button" onClick={handleDeleteAllCacheData} type="button">Golește Cache</button>
                </div>
                           
            </form>
        </div>
    );


};

export default CacheManager;