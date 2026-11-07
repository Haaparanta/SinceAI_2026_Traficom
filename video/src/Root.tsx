import { Composition } from "remotion";
import { Cut, FPS, cutTimeline } from "./Cut";

export const Root = () => {
  const { total } = cutTimeline();
  return (
    <Composition id="FilingRadarCut" component={Cut} durationInFrames={total} fps={FPS} width={1920} height={1080} />
  );
};
