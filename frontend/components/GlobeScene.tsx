"use client";
import { useEffect, useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Sphere, MeshDistortMaterial, Float, Sparkles } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

// Exchange locations [lon, lat] in radians (phi from north pole, theta from prime meridian)
const EXCHANGES = [
  { name: "NSE", phi: 1.1, theta: 1.33, color: "#00f0ff" },
  { name: "NYSE", phi: 0.9, theta: -1.3, color: "#00ff88" },
  { name: "LSE", phi: 0.9, theta: 0.0, color: "#8b5cf6" },
  { name: "TSE", phi: 0.6, theta: 2.4, color: "#ff8800" },
  { name: "SGX", phi: 1.1, theta: 1.8, color: "#ff4466" },
  { name: "ASX", phi: 1.7, theta: 2.5, color: "#00ffcc" },
];

function GlobeDot({ phi, theta, color }: { phi: number; theta: number; color: string }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      const scale = 1 + 0.4 * Math.sin(t * 2 + phi);
      ref.current.scale.setScalar(scale);
    }
  });

  const x = Math.sin(phi) * Math.cos(theta) * 2.05;
  const y = Math.cos(phi) * 2.05;
  const z = Math.sin(phi) * Math.sin(theta) * 2.05;

  return (
    <mesh ref={ref} position={[x, y, z]}>
      <sphereGeometry args={[0.04, 8, 8]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2} />
    </mesh>
  );
}

function Globe() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(() => { if (ref.current) ref.current.rotation.y += 0.002; });

  return (
    <group>
      {/* Core globe */}
      <Sphere ref={ref} args={[2, 64, 64]}>
        <MeshDistortMaterial
          color="#001a2e"
          roughness={0.8}
          metalness={0.1}
          distort={0.05}
          speed={1}
          transparent
          opacity={0.9}
          wireframe={false}
        />
      </Sphere>
      {/* Wireframe overlay */}
      <Sphere args={[2.01, 24, 24]}>
        <meshStandardMaterial color="#00f0ff" wireframe transparent opacity={0.06} />
      </Sphere>
      {/* Exchange dots */}
      {EXCHANGES.map((e) => (
        <GlobeDot key={e.name} phi={e.phi} theta={e.theta} color={e.color} />
      ))}
      <Sparkles count={80} scale={6} size={1} speed={0.3} color="#00f0ff" opacity={0.3} />
    </group>
  );
}

export default function GlobeScene() {
  return (
    <div style={{ width: "100%", height: "420px" }}>
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.8} color="#00f0ff" />
        <pointLight position={[-10, -5, -5]} intensity={0.3} color="#8b5cf6" />
        <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
          <Globe />
        </Float>
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.3} />
        <EffectComposer>
          <Bloom luminanceThreshold={0.4} intensity={0.6} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
