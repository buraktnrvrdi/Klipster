import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Next.js 16'nin core-web-vitals presetiyle gelen bu kural, mount
      // effect'i icinde HERHANGI bir senkron setState cagrisini (ör.
      // localStorage'da token yoksa erken cikip loading=false yapmak gibi
      // yaygin/zararsiz bir guard clause) hata sayiyor - projedeki tum
      // kullanimlari React Compiler'in henuz taslak asamasindaki bu
      // heuristigine gore yeniden yazmak gereksiz risk/karmasiklik katar.
      // Gercek bir "cascading render" sorunu degil, bu yuzden bilerek
      // kapatildi (bkz. app/page.tsx, davet, email-dogrula, profil,
      // ClipEditor, NavAuth, ParallaxStars).
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
