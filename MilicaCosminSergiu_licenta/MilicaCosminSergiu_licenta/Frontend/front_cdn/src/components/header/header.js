import React from 'react';
import './header.css';
import { Link } from 'react-router-dom';

function Header() {
    const isLoggedIn = localStorage.getItem('token') !== null;
    const userRole = localStorage.getItem('userRole');
    return (
        <div class="navbar">
            <div class="container">
                <a class="logo" href="/">
                    <img src="./logo.png" alt="Logo" />
                </a>
                <ul class="menu">
                    {!isLoggedIn && (
                        <>
                            <li><Link className='underline' to="/login">Login</Link></li>
                            <li><Link className='underline' to="/signup">Signup</Link></li>
                        </>
                    )}
                    {isLoggedIn && userRole == 'user'  && (
                        <>
                            <li><Link className='underline' to="/logout">LogOut</Link></li>
                            <li><Link className='underline' to="/add_site">NewSite</Link></li>
                            <li><Link className='underline' to="/my-sites">MySite</Link></li>
                            <li><Link className='underline' to="/profile"><img src="./usr.png" alt="profil" height={25} /></Link></li> 
                        </>
                    )}
                    
                    {isLoggedIn && userRole == 'admin' && (
                        <>
                            <li><Link className='underline' to="/logout">LogOut</Link></li>
                            <li><Link className='underline' to="/admin/trafic">Trafic</Link></li>
                            <li><Link className='underline' to="/admin/addedge">AddEdge</Link></li>
                            <li><Link className='underline' to="/admin/edgeservers">EdgeServer</Link></li>
                            <li><Link className='underline' to="/admin/edgeservers/banip">Ban Client</Link></li>
                            <li><Link className='underline' to="/profile"><img src="usr.png" alt="profil" height={25} /></Link></li>
                        </>
                    )}
                    
                </ul>
            </div>
        </div>
    );
};

export default Header;