import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    logout();
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');

  
    navigate('/login');
  };

  return (
    <div>
      <p>Logging out...</p>
    </div>
  );
}

export default Logout;