// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
import { ApolloServer } from '@apollo/server';
import { resolvers, typeDefs } from './schema';

export const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: true,
});
