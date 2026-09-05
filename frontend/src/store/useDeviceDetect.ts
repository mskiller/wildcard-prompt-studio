import { useState, useEffect } from 'react';

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isTouch: boolean;
  width: number;
  height: number;
  orientation: 'portrait' | 'landscape';
}

export function useDeviceDetect(): DeviceInfo {
  const getDeviceInfo = (): DeviceInfo => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1200;
    const height = typeof window !== 'undefined' ? window.innerHeight : 800;
    const isTouch = typeof window !== 'undefined' && 
      (window.matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0);
    
    const isMobile = width < 768 || (isTouch && width < 1024);
    const isTablet = width >= 768 && width <= 1024;
    const isDesktop = width > 1024 && !isTouch;

    return {
      isMobile,
      isTablet,
      isDesktop,
      isTouch,
      width,
      height,
      orientation: height > width ? 'portrait' : 'landscape',
    };
  };

  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>(getDeviceInfo());

  useEffect(() => {
    const handleResize = () => {
      setDeviceInfo(getDeviceInfo());
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return deviceInfo;
}
