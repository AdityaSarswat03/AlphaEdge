"use client";
import { useEffect, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function WavePlane() {
  const meshRef = useRef<THREE.Mesh>(null!);
  const geo = useRef<THREE.PlaneGeometry>(null!);

  useEffect(() => {
    geo.current = new THREE.PlaneGeometry(30, 30, 40, 40);
  }, []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    const pos = geo.current.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      pos.setZ(i, Math.sin(x * 0.4 + t * 0.5) * 0.3 + Math.sin(y * 0.3 + t * 0.4) * 0.2);
    }
    pos.needsUpdate = true;
    if (meshRef.current) meshRef.current.geometry = geo.current;
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2.5, 0, 0]} position={[0, -4, 0]}>
      <planeGeometry args={[30, 30, 40, 40]} ref={geo as any} />
      <meshStandardMaterial
        color="#001a2e"
        wireframe
        transparent
        opacity={0.25}
      />
    </mesh>
  );
}

export default function MeshBackground() {
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }}>
      <Canvas camera={{ position: [0, 6, 12], fov: 50 }}>
        <ambientLight intensity={0.3} color="#00f0ff" />
        <WavePlane />
      </Canvas>
    </div>
  );
}
