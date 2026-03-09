"use client";
import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Text } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

interface BarProps {
  x: number;
  height: number;
  color: string;
  label: string;
  price: number;
}

function PriceBar({ x, height, color, label, price }: BarProps) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) ref.current.rotation.y = Math.sin(t * 0.5) * 0.02;
  });

  return (
    <group position={[x, 0, 0]}>
      {/* Bar */}
      <mesh ref={ref} position={[0, height / 2, 0]}>
        <boxGeometry args={[0.8, height, 0.8]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.4} />
      </mesh>
      {/* Glow top */}
      <pointLight position={[0, height + 0.5, 0]} color={color} intensity={2} distance={4} />
    </group>
  );
}

function ReflectiveFloor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshStandardMaterial color="#060612" roughness={0.1} metalness={0.8} />
    </mesh>
  );
}

interface Props {
  currentPrice: number;
  predictedPrice: number;
  isUp: boolean;
}

export default function PriceBarsScene({ currentPrice, predictedPrice, isUp }: Props) {
  const maxPrice = Math.max(currentPrice, predictedPrice);
  const scale = 4 / maxPrice;
  const curH = currentPrice * scale;
  const predH = predictedPrice * scale;

  return (
    <div style={{ width: "100%", height: "380px" }}>
      <Canvas camera={{ position: [0, 4, 8], fov: 50 }} shadows>
        <ambientLight intensity={0.2} />
        <directionalLight position={[5, 10, 5]} intensity={0.5} castShadow />
        <pointLight position={[0, 8, 0]} intensity={0.4} color="#00f0ff" />

        <PriceBar x={-1.5} height={curH} color="#00f0ff" label="Current" price={currentPrice} />
        <PriceBar x={1.5} height={predH} color={isUp ? "#00ff88" : "#ff4466"} label="Predicted" price={predictedPrice} />

        <ReflectiveFloor />
        <OrbitControls enableZoom={false} enablePan={false} />
        <EffectComposer>
          <Bloom luminanceThreshold={0.3} intensity={0.8} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
