'use client';

import { useContext, useEffect, useState } from 'react';

import { fetchApi } from '@/app/lib/api';
import { JwtContext } from '@/app/lib/jwt-provider';

import LoginRequired from '@/app/lib/login-required';
import DiscordButton from '@/app/ui/discord-button';
import DiscordDisconnectButton from '@/app/ui/discord-disconnect-button';
import Navbar from '@/app/ui/navbar';

function SettingsPage() {
  const [jwt, setAndStoreJwt] = useContext(JwtContext);
  const [settings, setSettings] = useState<any>({});

  const fetchData = async () => {
    try {
      const response = await fetchApi(jwt, setAndStoreJwt, "settings/");
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const discordElement = settings.discord ? (
    <>
      <p>Discord: {settings.discord}</p>
      <DiscordDisconnectButton />
    </>
  ) : (
    <DiscordButton action='connect' />
  );

  return (
    <>
      <Navbar />
      <main className="container mx-auto mt-4">
        <h1 className="mb-4 font-black text-5xl">Settings</h1>
        {discordElement}
      </main>
    </>
  );

}

export default function Page() {
  return (
    <LoginRequired>
      <SettingsPage />
    </LoginRequired>
  );
}
