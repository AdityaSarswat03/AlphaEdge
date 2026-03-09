"use client";
import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

interface Props { sentiment: "positive" | "negative" | "neutral"; intensity: number; }

function ParticleSphere({ sentiment, intensity }: Props) {
  const points = useRef<THREE.Points>(null!);
  const count = 500;

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      pos[i * 3] = Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = Math.cos(phi);
      const c = sentiment === "positive"
        ? new THREE.Color("#00ff88")
        : sentiment === "negative"
        ? new THREE.Color("#ff4466")
        : new THREE.Color("#8b5cf6");
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    return geo;
  }, [sentiment]);

  useFrame(({ clock }) => {
    if (!points.current) return;
    const t = clock.getElapsedTime();
    const posAttr = points.current.geometry.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      const radius = 2 + Math.sin(t + i * 0.1) * 0.2 * intensity;
      posAttr.setXYZ(
        i,
        Math.sin(phi) * Math.cos(theta) * radius,
        Math.sin(phi) * Math.sin(theta) * radius,
        Math.cos(phi) * radius
      );
    }
    posAttr.needsUpdate = true;
    points.current.rotation.y = t * 0.1;
  });

  return (
    <points ref={points} geometry={geometry}>
      <pointsMaterial size={0.05} vertexColors sizeAttenuation transparent opacity={0.9} />
    </points>
  );
}

export default function SentimentSphere({ sentiment, intensity }: Props) {
  return (
    <div style={{ width: "100%", height: "350px" }}>
      <Canvas camera={{ position: [0, 0, 6], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight
          position={[0, 0, 0]}
          intensity={3}
          color={sentiment === "positive" ? "#00ff88" : sentiment === "negative" ? "#ff4466" : "#8b5cf6"}
          distance={8}
        />
        <ParticleSphere sentiment={sentiment} intensity={intensity} />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
        <EffectComposer>
          <Bloom luminanceThreshold={0.1} intensity={1.2} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
