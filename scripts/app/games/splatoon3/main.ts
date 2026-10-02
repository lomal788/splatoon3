import "./style.css";
import { boot } from "../../../../games/splatoon3/client/app.ts";

const root = document.getElementById("app");
if (root) void boot(root);
